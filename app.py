# app.py
# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

# --- Flask App Initialization & Configuration ---
app = Flask(__name__)
# IMPORTANT: Change this secret key in a real production environment!
app.config['SECRET_KEY'] = 'a_very_secret_key_for_flask_sessions'

# --- Database Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'db_user_name',
    'password': 'db_user_password',
    'database': 'grocery_db'
}

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to /login if user is not authenticated

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'])
    return None

# --- Database Connection ---
def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

# --- Constants for Forms ---
CATEGORIES = ['Dairy & Eggs', 'Bakery', 'Meat & Fish', 'Produce', 'Spices', 'Pulses', 'Grains', 'Condiments & Sauces', 'Baking', 'Breakfast & Cereal', 'Snacks', 'Frozen Foods', 'Beverages', 'Household & Cleaning','Personal Care', 'Other']
UNITS = ['Count', 'kg', 'g', 'liters', 'ml', 'Packet', 'Bottle', 'Other']
STATUSES = ['Running low', 'In-Stock', 'Excess', 'Not Needed Anymore']

# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed.', 'danger')
            return render_template('login.html')

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(id=user_data['id'], username=user_data['username'])
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed.', 'danger')
            return render_template('register.html')

        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Main Application Routes (Protected) ---

@app.route('/')
@login_required
def index():
    """Displays the main grocery list for the logged-in user."""
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM groceries WHERE user_id = %s"
    params = [current_user.id]

    if search_query:
        sql += " AND name LIKE %s"
        params.append(f"%{search_query}%")
    
    sql += " ORDER BY category ASC, name ASC"
    cursor.execute(sql, tuple(params))
    items = cursor.fetchall()
    conn.close()

    grouped_items = {}
    for item in items:
        if item.get('expiry_date'):
            days = (item['expiry_date'] - datetime.now().date()).days
            item['days_to_expiry'] = days if days >= 0 else 'Expired'
        else:
            item['days_to_expiry'] = 'N/A'
        
        category = item['category']
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item)

    return render_template('index.html', items=items, grouped_items=grouped_items, search_query=search_query)

@app.route('/dashboard')
@login_required
def dashboard():
    """Displays the dashboard with metrics for the logged-in user."""
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)
    user_id = current_user.id
    
    # 1. Items by Status
    cursor.execute("SELECT status, COUNT(*) as count FROM groceries WHERE user_id = %s GROUP BY status", (user_id,))
    items_by_status = cursor.fetchall()
    
    # 2. Items by Category
    cursor.execute("SELECT category, COUNT(*) as count FROM groceries WHERE user_id = %s GROUP BY category ORDER BY count DESC", (user_id,))
    items_by_category = cursor.fetchall()
    
    # 3. Upcoming Expiries (next 7 days)
    today = date.today()
    next_week = today + timedelta(days=7)
    cursor.execute("SELECT name, expiry_date FROM groceries WHERE user_id = %s AND expiry_date BETWEEN %s AND %s ORDER BY expiry_date ASC", (user_id, today, next_week))
    upcoming_expiries = cursor.fetchall()
    
    # 4. Perishable vs Non-Perishable
    cursor.execute("SELECT type, COUNT(*) as count FROM groceries WHERE user_id = %s GROUP BY type", (user_id,))
    item_types = cursor.fetchall()

    # 5. Summary Cards Data
    cursor.execute("SELECT COUNT(*) as total_items FROM groceries WHERE user_id = %s", (user_id,))
    total_items = cursor.fetchone()['total_items']
    
    cursor.execute("SELECT COUNT(*) as running_low FROM groceries WHERE user_id = %s AND status = 'Running low'", (user_id,))
    running_low_count = cursor.fetchone()['running_low']

    cursor.execute("SELECT COUNT(*) as expired_count FROM groceries WHERE user_id = %s AND expiry_date < %s", (user_id, today))
    expired_count = cursor.fetchone()['expired_count']

    conn.close()

    # Prepare data for Chart.js
    status_data = {'labels': [s['status'] for s in items_by_status], 'data': [s['count'] for s in items_by_status]}
    category_data = {'labels': [c['category'] for c in items_by_category], 'data': [c['count'] for c in items_by_category]}
    type_data = {'labels': [t['type'] for t in item_types], 'data': [t['count'] for t in item_types]}

    summary_cards = {
        'total_items': total_items,
        'running_low': running_low_count,
        'expired_count': expired_count
    }

    return render_template('dashboard.html', 
                           status_data=status_data, 
                           category_data=category_data,
                           type_data=type_data,
                           upcoming_expiries=upcoming_expiries,
                           summary_cards=summary_cards)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """Handles adding a new grocery item for the logged-in user."""
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        item_type = request.form['type']
        quantity = float(request.form['quantity'])
        quantity_unit = request.form['quantity_unit']
        status = request.form['status']
        is_essential = 'is_essential' in request.form
        purchase_date = request.form['purchase_date'] or None
        expiry_date = request.form['expiry_date'] or None

        conn = get_db_connection()
        if not conn: return "Error: Could not connect to the database.", 500
        cursor = conn.cursor()
        sql = """
            INSERT INTO groceries (user_id, name, category, type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        val = (current_user.id, name, category, item_type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_item.html', categories=CATEGORIES, units=UNITS, statuses=STATUSES)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    """Handles editing an item, ensuring it belongs to the logged-in user."""
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("SELECT id FROM groceries WHERE id = %s AND user_id = %s", (id, current_user.id))
        if not cursor.fetchone():
            conn.close()
            return "Unauthorized", 403

        name = request.form['name']
        category = request.form['category']
        item_type = request.form['type']
        quantity = float(request.form['quantity'])
        quantity_unit = request.form['quantity_unit']
        status = request.form['status']
        is_essential = 'is_essential' in request.form
        purchase_date = request.form['purchase_date'] or None
        expiry_date = request.form['expiry_date'] or None

        sql = """
            UPDATE groceries SET name=%s, category=%s, type=%s, quantity=%s, quantity_unit=%s, status=%s, is_essential=%s, purchase_date=%s, expiry_date=%s
            WHERE id = %s AND user_id = %s
        """
        val = (name, category, item_type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date, id, current_user.id)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM groceries WHERE id = %s AND user_id = %s", (id, current_user.id))
    item = cursor.fetchone()
    conn.close()
    if not item:
        return "Item not found or you don't have permission to edit it.", 404
        
    return render_template('edit_item.html', item=item, categories=CATEGORIES, units=UNITS, statuses=STATUSES)

@app.route('/delete/<int:id>')
@login_required
def delete_item(id):
    """Handles deleting an item, ensuring it belongs to the logged-in user."""
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groceries WHERE id = %s AND user_id = %s", (id, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/shopping_list')
@login_required
def shopping_list():
    """Displays items that are running low or expired, separated by priority."""
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)
    
    user_id = current_user.id
    today = date.today()
    
    essential_query = "SELECT * FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = TRUE AND user_id = %s ORDER BY category ASC, name ASC"
    cursor.execute(essential_query, (today, user_id))
    essential_items_flat = cursor.fetchall()
    
    optional_query = "SELECT * FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = FALSE AND user_id = %s ORDER BY category ASC, name ASC"
    cursor.execute(optional_query, (today, user_id))
    optional_items_flat = cursor.fetchall()
    
    conn.close()

    # Add a 'reason' for each item being on the list
    for item in essential_items_flat + optional_items_flat:
        is_expired = item.get('expiry_date') and item['expiry_date'] < today
        item['reason'] = 'Expired' if is_expired else 'Running low'

    # Grouping logic
    grouped_essential = {c: [i for i in essential_items_flat if i['category'] == c] for c in {i['category'] for i in essential_items_flat}}
    grouped_optional = {c: [i for i in optional_items_flat if i['category'] == c] for c in {i['category'] for i in optional_items_flat}}

    return render_template('shopping_list.html', 
                           essential_items=essential_items_flat, 
                           optional_items=optional_items_flat,
                           grouped_essential_items=grouped_essential,
                           grouped_optional_items=grouped_optional)

@app.route('/export_shopping_list')
@login_required
def export_shopping_list():
    """Generates a printable shopping list for items that are running low or expired."""
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)
    
    user_id = current_user.id
    today = date.today()

    essential_query = "SELECT name FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = TRUE AND user_id = %s ORDER BY name ASC"
    cursor.execute(essential_query, (today, user_id))
    essential_items = cursor.fetchall()
    
    optional_query = "SELECT name FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = FALSE AND user_id = %s ORDER BY name ASC"
    cursor.execute(optional_query, (today, user_id))
    optional_items = cursor.fetchall()
    
    conn.close()
    export_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    return render_template('export_checklist.html', essential_items=essential_items, optional_items=optional_items, export_time=export_time)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
