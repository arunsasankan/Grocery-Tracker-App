# app.py
# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps

# --- Flask App Initialization & Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secret_key_for_flask_sessions'

# --- Predefined Admin Users ---
# Any username in this list will be given admin rights upon registration.
ADMIN_USERS = ['admin', 'superuser'] 

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
login_manager.login_view = 'login'

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, role, household_id, household_name=None):
        self.id = id
        self.username = username
        self.role = role
        self.household_id = household_id
        self.household_name = household_name

    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT u.id, u.username, r.name as role, u.household_id, h.name as household_name
        FROM users u 
        JOIN roles r ON u.role_id = r.id 
        LEFT JOIN households h ON u.household_id = h.id
        WHERE u.id = %s
    """
    cursor.execute(sql, (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], role=user_data['role'], household_id=user_data['household_id'], household_name=user_data['household_name'])
    return None

# --- Database Connection ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

# --- Custom Decorator for Admin Routes ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            return "Unauthorized", 403
        return f(*args, **kwargs)
    return decorated_function

# --- Constants for Forms ---
CATEGORIES = ['Dairy & Eggs', 'Bakery', 'Meat & Fish', 'Produce', 'Spices', 'Pulses', 'Grains', 'Condiments & Sauces', 'Baking', 'Breakfast & Cereal', 'Snacks', 'Frozen Foods', 'Beverages', 'Household & Cleaning', 'Personal Care', 'Other']
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
        sql = """
            SELECT u.*, r.name as role, h.name as household_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            LEFT JOIN households h ON u.household_id = h.id
            WHERE u.username = %s
        """
        cursor.execute(sql, (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(id=user_data['id'], username=user_data['username'], role=user_data['role'], household_id=user_data['household_id'], household_name=user_data['household_name'])
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
        
        cursor = conn.cursor(dictionary=True)
        
        # Determine role
        role_name = 'admin' if username in ADMIN_USERS else 'user'
        cursor.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
        role = cursor.fetchone()
        if not role:
            conn.close()
            flash('Error: User roles not set up correctly in the database.', 'danger')
            return render_template('register.html')
        role_id = role['id']

        try:
            cursor.execute("INSERT INTO users (username, password, role_id) VALUES (%s, %s, %s)", (username, hashed_password, role_id))
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

# --- Admin Routes ---

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)

    # Get stats for admin dashboard
    cursor.execute("SELECT COUNT(*) as count FROM households")
    total_households = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE household_id IS NULL")
    unassigned_users = cursor.fetchone()['count']

    conn.close()

    stats = {
        'total_households': total_households,
        'total_users': total_users,
        'unassigned_users': unassigned_users
    }

    return render_template('admin_dashboard.html', stats=stats)

@app.route('/admin/households', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_households():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        household_name = request.form['household_name']
        if household_name:
            try:
                cursor.execute("INSERT INTO households (name) VALUES (%s)", (household_name,))
                conn.commit()
                flash(f"Household '{household_name}' created successfully.", 'success')
            except mysql.connector.IntegrityError:
                flash(f"Household '{household_name}' already exists.", 'danger')
        return redirect(url_for('manage_households'))

    cursor.execute("SELECT * FROM households ORDER BY name ASC")
    households = cursor.fetchall()
    conn.close()
    return render_template('manage_households.html', households=households)

@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT u.id, u.username, r.name as role, h.name as household_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        LEFT JOIN households h ON u.household_id = h.id
        ORDER BY u.username ASC
    """
    cursor.execute(sql)
    users = cursor.fetchall()
    conn.close()
    return render_template('manage_users.html', users=users)

@app.route('/admin/assign_household/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_household(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        household_id = request.form.get('household_id')
        # If "None" is selected, set household_id to NULL
        if household_id == "None":
            household_id = None
        
        cursor.execute("UPDATE users SET household_id = %s WHERE id = %s", (household_id, user_id))
        conn.commit()
        conn.close()
        flash('User household updated.', 'success')
        return redirect(url_for('manage_users'))

    cursor.execute("SELECT id, username, household_id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    cursor.execute("SELECT id, name FROM households ORDER BY name ASC")
    households = cursor.fetchall()
    
    conn.close()
    
    if not user:
        return "User not found", 404
        
    return render_template('assign_household.html', user=user, households=households)


# --- Main Application Routes (Protected) ---

@app.route('/')
@login_required
def index():
    if not current_user.household_id:
        if current_user.is_admin():
             flash('You are an admin. Please create a household and assign yourself to it to view groceries.', 'info')
        else:
            flash('You are not yet assigned to a household. Please contact an admin.', 'warning')
        return render_template('index.html', items=[], grouped_items={})

    search_query = request.args.get('search', '')
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT g.*, u_created.username as created_by_user, u_modified.username as modified_by_user FROM groceries g JOIN users u_created ON g.created_by = u_created.id LEFT JOIN users u_modified ON g.modified_by = u_modified.id WHERE g.household_id = %s"
    params = [current_user.household_id]

    if search_query:
        sql += " AND g.name LIKE %s"
        params.append(f"%{search_query}%")
    
    sql += " ORDER BY g.category ASC, g.name ASC"
    cursor.execute(sql, tuple(params))
    items = cursor.fetchall()
    conn.close()

    grouped_items = {}
    for item in items:
        if item.get('expiry_date'):
            days = (item['expiry_date'] - date.today()).days
            item['days_to_expiry'] = days if days >= 0 else 'Expired'
        else:
            item['days_to_expiry'] = 'N/A'
        
        category = item['category']
        if category not in grouped_items:
            grouped_items[category] = []
        grouped_items[category].append(item)

    return render_template('index.html', items=items, grouped_items=grouped_items, search_query=search_query)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if not current_user.household_id:
        flash('You must be in a household to add items.', 'danger')
        return redirect(url_for('index'))

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
            INSERT INTO groceries (household_id, name, category, type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date, created_by, modified_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        val = (current_user.household_id, name, category, item_type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date, current_user.id, current_user.id)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_item.html', categories=CATEGORIES, units=UNITS, statuses=STATUSES)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        cursor.execute("SELECT id FROM groceries WHERE id = %s AND household_id = %s", (id, current_user.household_id))
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
            UPDATE groceries SET name=%s, category=%s, type=%s, quantity=%s, quantity_unit=%s, status=%s, is_essential=%s, purchase_date=%s, expiry_date=%s, modified_by=%s
            WHERE id = %s AND household_id = %s
        """
        val = (name, category, item_type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date, current_user.id, id, current_user.household_id)
        cursor.execute(sql, val)
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cursor.execute("SELECT * FROM groceries WHERE id = %s AND household_id = %s", (id, current_user.household_id))
    item = cursor.fetchone()
    conn.close()
    if not item:
        return "Item not found or you don't have permission to edit it.", 404
        
    return render_template('edit_item.html', item=item, categories=CATEGORIES, units=UNITS, statuses=STATUSES)

@app.route('/delete/<int:id>')
@login_required
def delete_item(id):
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groceries WHERE id = %s AND household_id = %s", (id, current_user.household_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.household_id:
        flash('You must be in a household to view the dashboard.', 'danger')
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)
    household_id = current_user.household_id
    
    cursor.execute("SELECT status, COUNT(*) as count FROM groceries WHERE household_id = %s GROUP BY status", (household_id,))
    items_by_status = cursor.fetchall()
    
    cursor.execute("SELECT category, COUNT(*) as count FROM groceries WHERE household_id = %s GROUP BY category ORDER BY count DESC", (household_id,))
    items_by_category = cursor.fetchall()
    
    today = date.today()
    next_week = today + timedelta(days=7)
    cursor.execute("SELECT name, expiry_date FROM groceries WHERE household_id = %s AND expiry_date BETWEEN %s AND %s ORDER BY expiry_date ASC", (household_id, today, next_week))
    upcoming_expiries = cursor.fetchall()
    
    cursor.execute("SELECT type, COUNT(*) as count FROM groceries WHERE household_id = %s GROUP BY type", (household_id,))
    item_types = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total_items FROM groceries WHERE household_id = %s", (household_id,))
    total_items = cursor.fetchone()['total_items']
    
    cursor.execute("SELECT COUNT(*) as running_low FROM groceries WHERE household_id = %s AND status = 'Running low'", (household_id,))
    running_low_count = cursor.fetchone()['running_low']

    cursor.execute("SELECT COUNT(*) as expired_count FROM groceries WHERE household_id = %s AND expiry_date < %s", (household_id, today))
    expired_count = cursor.fetchone()['expired_count']

    conn.close()

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

@app.route('/shopping_list')
@login_required
def shopping_list():
    if not current_user.household_id:
        flash('You must be in a household to view the shopping list.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)
    
    household_id = current_user.household_id
    today = date.today()
    
    essential_query = "SELECT * FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = TRUE AND household_id = %s ORDER BY category ASC, name ASC"
    cursor.execute(essential_query, (today, household_id))
    essential_items_flat = cursor.fetchall()
    
    optional_query = "SELECT * FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = FALSE AND household_id = %s ORDER BY category ASC, name ASC"
    cursor.execute(optional_query, (today, household_id))
    optional_items_flat = cursor.fetchall()
    
    conn.close()

    for item in essential_items_flat + optional_items_flat:
        is_expired = item.get('expiry_date') and item['expiry_date'] < today
        item['reason'] = 'Expired' if is_expired else 'Running low'

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
    if not current_user.household_id:
        flash('You must be in a household to export a shopping list.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    if not conn: return "Error: Could not connect to the database.", 500
    cursor = conn.cursor(dictionary=True)
    
    household_id = current_user.household_id
    today = date.today()

    essential_query = "SELECT name FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = TRUE AND household_id = %s ORDER BY name ASC"
    cursor.execute(essential_query, (today, household_id))
    essential_items = cursor.fetchall()
    
    optional_query = "SELECT name FROM groceries WHERE (status = 'Running low' OR expiry_date < %s) AND is_essential = FALSE AND household_id = %s ORDER BY name ASC"
    cursor.execute(optional_query, (today, household_id))
    optional_items = cursor.fetchall()
    
    conn.close()
    export_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")

    return render_template('export_checklist.html', essential_items=essential_items, optional_items=optional_items, export_time=export_time)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
