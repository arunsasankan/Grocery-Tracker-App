# app.py
# Import necessary libraries
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
import random
import string

# --- Flask App Initialization & Configuration ---
import config

app = Flask(__name__)
# Load configuration from the config file
app.config['SECRET_KEY'] = config.SECRET_KEY
DB_CONFIG = config.DB_CONFIG

# --- Flask-Login Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- User Model ---
class User(UserMixin):
    def __init__(self, id, username, is_admin=False):
        self.id = id
        self.username = username
        self.is_admin_flag = is_admin
    
    def is_admin(self):
        return self.is_admin_flag

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], is_admin=user_data.get('is_superadmin', False))
    return None

# --- Database Connection ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=3306,
        unix_socket='/var/lib/mysql/mysql.sock'
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

# --- Constants for Forms ---
CATEGORIES = ['Dairy & Eggs', 'Bakery', 'Meat & Fish', 'Produce', 'Spices', 'Pulses', 'Grains', 'Condiments', 'Baking', 'Breakfast & Cereal', 'Snacks', 'Frozen Foods', 'Beverages', 'Household & Personal Care', 'Other']
UNITS = ['Count', 'kg', 'g', 'liters', 'ml', 'Packet', 'Bottle', 'Other']
STATUSES = ['Running low', 'In-Stock', 'Excess', 'Buy More']

# --- Helper function for audit logging ---
def log_action(user_id, action, details="", household_id=None):
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("INSERT INTO audit_log (user_id, household_id, action, details) VALUES (%s, %s, %s, %s)",
                   (user_id, household_id, action, details))
    conn.commit()
    conn.close()

def generate_household_code(length=8):
    """Generates a random alphanumeric code for households."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- Decorators ---
def household_member_required(f):
    @wraps(f)
    def decorated_function(household_id, *args, **kwargs):
        conn = get_db_connection()
        if not conn: return "Error", 500
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM user_households WHERE user_id = %s AND household_id = %s AND status = 'approved'", (current_user.id, household_id))
        membership = cursor.fetchone()
        conn.close()
        if not membership:
            flash("You are not a member of this household.", "danger")
            return redirect(url_for('households'))
        return f(household_id, *args, **kwargs)
    return decorated_function

def household_admin_required(f):
    @wraps(f)
    def decorated_function(household_id, *args, **kwargs):
        conn = get_db_connection()
        if not conn: return "Error", 500
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT admin_id FROM households WHERE id = %s", (household_id,))
        household = cursor.fetchone()
        conn.close()
        if not household or household['admin_id'] != current_user.id:
            flash("You are not the admin of this household.", "danger")
            return redirect(url_for('households'))
        return f(household_id, *args, **kwargs)
    return decorated_function

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
            user = User(id=user_data['id'], username=user_data['username'], is_admin=user_data.get('is_superadmin', False))
            login_user(user)
            log_action(user.id, "User Login")
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        email = request.form['email']
        mobile = request.form['mobile_number']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed.', 'danger')
            return render_template('register.html')
        try:
            cursor = conn.cursor()
            sql = "INSERT INTO users (username, password, full_name, email, mobile_number) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (username, hashed_password, full_name, email, mobile))
            conn.commit()
            log_action(cursor.lastrowid, "User Registered")
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError as err:
            if 'username' in str(err): flash('Username already exists.', 'danger')
            elif 'email' in str(err): flash('Email address is already registered.', 'danger')
            else: flash('An unexpected error occurred.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    log_action(current_user.id, "User Logout")
    logout_user()
    return redirect(url_for('login'))

# --- Household Management Routes ---
@app.route('/households')
@login_required
def households():
    conn = get_db_connection()
    if not conn: return "Error connecting to database", 500
    cursor = conn.cursor(dictionary=True)
    search_term = request.args.get('search', '')
    cursor.execute("SELECT h.*, u.username as admin_name FROM households h JOIN user_households uh ON h.id = uh.household_id JOIN users u ON h.admin_id = u.id WHERE uh.user_id = %s AND uh.status = 'approved'", (current_user.id,))
    my_households = cursor.fetchall()
    other_households_query = "SELECT h.*, u.username as admin_name, uh.status as request_status FROM households h JOIN users u ON h.admin_id = u.id LEFT JOIN user_households uh ON h.id = uh.household_id AND uh.user_id = %s WHERE h.id NOT IN (SELECT household_id FROM user_households WHERE user_id = %s AND status = 'approved')"
    params = [current_user.id, current_user.id]
    if search_term:
        other_households_query += " AND (h.name LIKE %s OR h.household_code = %s)"
        params.extend([f"%{search_term}%", search_term])
    cursor.execute(other_households_query, tuple(params))
    other_households = cursor.fetchall()
    conn.close()
    return render_template('households.html', my_households=my_households, other_households=other_households, search_term=search_term)

@app.route('/create_household', methods=['POST'])
@login_required
def create_household():
    name = request.form['name']
    address = request.form['address']
    location = request.form['location']
    code = generate_household_code()

    conn = get_db_connection()
    if not conn: return "Error connecting to database", 500
    cursor = conn.cursor()
    cursor.execute("INSERT INTO households (name, address, location, admin_id, household_code) VALUES (%s, %s, %s, %s, %s)",
                   (name, address, location, current_user.id, code))
    household_id = cursor.lastrowid
    cursor.execute("INSERT INTO user_households (user_id, household_id, status) VALUES (%s, %s, 'approved')",
                   (current_user.id, household_id))
    conn.commit()
    log_action(current_user.id, "Household Created", f"Name: {name}, Code: {code}", household_id)
    conn.close()
    flash(f"Household '{name}' created successfully!", 'success')
    return redirect(url_for('households'))

@app.route('/request_join/<int:household_id>', methods=['POST'])
@login_required
def request_join_household(household_id):
    conn = get_db_connection()
    if not conn: return "Error", 500
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO user_households (user_id, household_id, status) VALUES (%s, %s, 'pending')", (current_user.id, household_id))
        conn.commit()
        log_action(current_user.id, "Join Request Sent", f"Requested to join household ID {household_id}", household_id)
        flash("Your request to join the household has been sent.", 'success')
    except mysql.connector.IntegrityError:
        flash("You have already sent a request to join this household.", 'warning')
    finally:
        conn.close()
    return redirect(url_for('households'))

@app.route('/manage_household/<int:household_id>', methods=['GET', 'POST'])
@login_required
@household_admin_required
def manage_household(household_id):
    conn = get_db_connection()
    if not conn: return "Error", 500
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        location = request.form['location']
        cursor.execute("UPDATE households SET name = %s, address = %s, location = %s WHERE id = %s",
                       (name, address, location, household_id))
        conn.commit()
        log_action(current_user.id, "Household Details Updated", f"Updated name to {name}", household_id)
        flash("Household details updated successfully.", 'success')
        return redirect(url_for('manage_household', household_id=household_id))

    cursor.execute("SELECT * FROM households WHERE id = %s", (household_id,))
    household = cursor.fetchone()
    cursor.execute("SELECT u.id, u.username, u.full_name, u.email FROM users u JOIN user_households uh ON u.id = uh.user_id WHERE uh.household_id = %s AND uh.status = 'approved'", (household_id,))
    members = cursor.fetchall()
    cursor.execute("SELECT u.id, u.username, u.full_name, u.email FROM users u JOIN user_households uh ON u.id = uh.user_id WHERE uh.household_id = %s AND uh.status = 'pending'", (household_id,))
    pending_requests = cursor.fetchall()
    conn.close()
    return render_template('manage_household.html', household=household, members=members, pending_requests=pending_requests)

@app.route('/manage_request/<int:household_id>/<int:user_id>/<action>')
@login_required
@household_admin_required
def manage_request(household_id, user_id, action):
    conn = get_db_connection()
    if not conn: return "Error", 500
    cursor = conn.cursor()
    if action == 'approve':
        cursor.execute("UPDATE user_households SET status = 'approved' WHERE user_id = %s AND household_id = %s", (user_id, household_id))
        log_action(current_user.id, "Approved Join Request", f"User ID {user_id} approved", household_id)
        flash("User has been added to the household.", 'success')
    elif action == 'deny':
        cursor.execute("DELETE FROM user_households WHERE user_id = %s AND household_id = %s", (user_id, household_id))
        log_action(current_user.id, "Denied Join Request", f"User ID {user_id} denied", household_id)
        flash("Request has been denied.", 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('manage_household', household_id=household_id))

@app.route('/remove_member/<int:household_id>/<int:user_id>')
@login_required
@household_admin_required
def remove_member(household_id, user_id):
    if user_id == current_user.id:
        flash("Admins cannot remove themselves from the household.", "danger")
        return redirect(url_for('manage_household', household_id=household_id))

    conn = get_db_connection()
    if not conn: return "Error", 500
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_households WHERE user_id = %s AND household_id = %s", (user_id, household_id))
    conn.commit()
    conn.close()
    log_action(current_user.id, "Removed Member", f"Removed user ID {user_id}", household_id)
    flash("Member has been removed from the household.", "success")
    return redirect(url_for('manage_household', household_id=household_id))

@app.route('/delete_household/<int:household_id>', methods=['POST'])
@login_required
@household_admin_required
def delete_household(household_id):
    conn = get_db_connection()
    if not conn: return "Error", 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT name FROM households WHERE id = %s", (household_id,))
    household = cursor.fetchone()
    log_action(current_user.id, "Household Deleted", f"Deleted household '{household['name']}' (ID: {household_id})")
    cursor.execute("DELETE FROM households WHERE id = %s", (household_id,))
    conn.commit()
    conn.close()
    flash(f"Household '{household['name']}' has been permanently deleted.", "success")
    return redirect(url_for('households'))

# --- Main Application Routes ---
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    if not conn: return "Error", 500
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT household_id FROM user_households WHERE user_id = %s AND status = 'approved'", (current_user.id,))
    user_households = cursor.fetchall()
    conn.close()
    if not user_households:
        flash("Please create or join a household to start tracking groceries.", 'info')
        return redirect(url_for('households'))
    return redirect(url_for('view_household', household_id=user_households[0]['household_id']))

@app.route('/household/<int:household_id>')
@login_required
@household_member_required
def view_household(household_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, household_code FROM households WHERE id IN (SELECT household_id FROM user_households WHERE user_id = %s AND status = 'approved')", (current_user.id,))
    user_households = cursor.fetchall()
    search_query = request.args.get('search', '')
    sql = "SELECT g.*, p.icon_class, u_created.username as created_by_user, u_modified.username as modified_by_user FROM groceries g LEFT JOIN pantry_items p ON g.name = p.name LEFT JOIN users u_created ON g.created_by = u_created.id LEFT JOIN users u_modified ON g.modified_by = u_modified.id WHERE g.household_id = %s"
    params = [household_id]
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
    return render_template('index.html', items=items, grouped_items=grouped_items, search_query=search_query, household_id=household_id, user_households=user_households, units=UNITS, statuses=STATUSES)

@app.route('/household/<int:household_id>/add', methods=['GET', 'POST'])
@login_required
@household_member_required
def add_item(household_id):
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        item_type = request.form['type']
        quantity = float(request.form['quantity'])
        quantity_unit = request.form['quantity_unit']
        status = request.form['status']
        is_essential = 'is_essential' in request.form
        purchase_date_str = request.form.get('purchase_date')
        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date() if purchase_date_str else date.today()
        expiry_date = request.form['expiry_date'] or None

        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO groceries (household_id, name, category, type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (household_id, name, category, item_type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date, current_user.id)
        cursor.execute(sql, val)
        conn.commit()
        log_action(current_user.id, "Item Added", f"Item: {name}", household_id)
        conn.close()
        return redirect(url_for('view_household', household_id=household_id))
    return render_template('add_item.html', categories=CATEGORIES, units=UNITS, statuses=STATUSES, household_id=household_id)

@app.route('/household/<int:household_id>/update_item/<int:item_id>', methods=['POST'])
@login_required
@household_member_required
def update_item_inline(household_id, item_id):
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')

    allowed_fields = ['quantity', 'quantity_unit', 'status', 'is_essential']
    if not field or field not in allowed_fields:
        return jsonify({'success': False, 'message': 'Invalid field.'}), 400

    if field == 'is_essential':
        value = bool(value)

    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed.'}), 500
    
    cursor = conn.cursor()
    try:
        sql = f"UPDATE groceries SET {field} = %s, modified_by = %s WHERE id = %s AND household_id = %s"
        cursor.execute(sql, (value, current_user.id, item_id, household_id))
        conn.commit()
        log_action(current_user.id, "Item Inline Update", f"Updated {field} for item ID {item_id}", household_id)
        return jsonify({'success': True, 'message': 'Item updated successfully.'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/household/<int:household_id>/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@household_member_required
def edit_item(household_id, item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
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
        sql = "UPDATE groceries SET name=%s, category=%s, type=%s, quantity=%s, quantity_unit=%s, status=%s, is_essential=%s, purchase_date=%s, expiry_date=%s, modified_by=%s WHERE id = %s AND household_id = %s"
        val = (name, category, item_type, quantity, quantity_unit, status, is_essential, purchase_date, expiry_date, current_user.id, item_id, household_id)
        cursor.execute(sql, val)
        conn.commit()
        log_action(current_user.id, "Item Edited", f"Item ID: {item_id}", household_id)
        conn.close()
        return redirect(url_for('view_household', household_id=household_id))
    cursor.execute("SELECT * FROM groceries WHERE id = %s AND household_id = %s", (item_id, household_id))
    item = cursor.fetchone()
    conn.close()
    if not item:
        return "Item not found", 404
    return render_template('edit_item.html', item=item, categories=CATEGORIES, units=UNITS, statuses=STATUSES, household_id=household_id)

@app.route('/household/<int:household_id>/delete/<int:item_id>')
@login_required
@household_member_required
def delete_item(household_id, item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groceries WHERE id = %s AND household_id = %s", (item_id, household_id))
    conn.commit()
    log_action(current_user.id, "Item Deleted", f"Item ID: {item_id}", household_id)
    conn.close()
    return redirect(url_for('view_household', household_id=household_id))

@app.route('/household/<int:household_id>/dashboard')
@login_required
@household_member_required
def dashboard(household_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
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
    summary_cards = {'total_items': total_items, 'running_low': running_low_count, 'expired_count': expired_count}
    return render_template('dashboard.html', status_data=status_data, category_data=category_data, type_data=type_data, upcoming_expiries=upcoming_expiries, summary_cards=summary_cards, household_id=household_id)

@app.route('/household/<int:household_id>/shopping_list')
@login_required
@household_member_required
def shopping_list(household_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = date.today()
    
    shopping_list_query = "SELECT g.*, p.icon_class FROM groceries g LEFT JOIN pantry_items p ON g.name = p.name WHERE g.household_id = %s AND (g.status IN ('Running low', 'Buy More') OR g.expiry_date < %s) ORDER BY g.is_essential DESC, g.category ASC, g.name ASC"
    cursor.execute(shopping_list_query, (household_id, today))
    all_shopping_items = cursor.fetchall()
    
    conn.close()

    essential_items_flat = []
    optional_items_flat = []

    for item in all_shopping_items:
        is_expired = item.get('expiry_date') and item['expiry_date'] < today
        if is_expired:
            item['reason'] = 'Expired'
        elif item['status'] == 'Buy More':
            item['reason'] = 'Buy More'
        else:
            item['reason'] = 'Running low'
        
        if item['is_essential']:
            essential_items_flat.append(item)
        else:
            optional_items_flat.append(item)

    grouped_essential = {c: [i for i in essential_items_flat if i['category'] == c] for c in {i['category'] for i in essential_items_flat}}
    grouped_optional = {c: [i for i in optional_items_flat if i['category'] == c] for c in {i['category'] for i in optional_items_flat}}

    return render_template('shopping_list.html', 
                           essential_items=essential_items_flat, 
                           optional_items=optional_items_flat,
                           grouped_essential_items=grouped_essential,
                           grouped_optional_items=grouped_optional,
                           household_id=household_id)

@app.route('/household/<int:household_id>/export_shopping_list')
@login_required
@household_member_required
def export_shopping_list(household_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    today = date.today()
    
    shopping_list_query = "SELECT name, is_essential FROM groceries WHERE household_id = %s AND (status IN ('Running low', 'Buy More') OR expiry_date < %s) ORDER BY is_essential DESC, name ASC"
    cursor.execute(shopping_list_query, (household_id, today))
    all_items = cursor.fetchall()
    
    essential_items = [item for item in all_items if item['is_essential']]
    optional_items = [item for item in all_items if not item['is_essential']]
    
    conn.close()
    export_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    return render_template('export_checklist.html', essential_items=essential_items, optional_items=optional_items, export_time=export_time, household_id=household_id)

@app.route('/household/<int:household_id>/pantry', methods=['GET', 'POST'])
@login_required
@household_member_required
def pantry(household_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        items_to_add = request.form.getlist('pantry_item_id')
        
        for item_id in items_to_add:
            quantity = float(request.form.get(f'quantity_{item_id}', 1.0))
            quantity_unit = request.form.get(f'quantity_unit_{item_id}', 'Count')
            status = request.form.get(f'status_{item_id}', 'In-Stock')

            cursor.execute("SELECT name, type, category FROM pantry_items WHERE id = %s", (item_id,))
            pantry_item = cursor.fetchone()
            if pantry_item:
                sql = "INSERT INTO groceries (household_id, name, category, type, quantity, quantity_unit, status, created_by, purchase_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                val = (household_id, pantry_item['name'], pantry_item['category'], pantry_item['type'], quantity, quantity_unit, status, current_user.id, date.today())
                try:
                    cursor.execute(sql, val)
                except mysql.connector.IntegrityError:
                    pass # Item might already exist, ignore for now
        conn.commit()
        log_action(current_user.id, "Added from Pantry", f"Added {len(items_to_add)} items.", household_id)
        flash(f"Added {len(items_to_add)} items from the master pantry list.", 'success')
        conn.close()
        return redirect(url_for('view_household', household_id=household_id))

    # GET request logic
    cursor.execute("SELECT name FROM groceries WHERE household_id = %s", (household_id,))
    household_items = {row['name'] for row in cursor.fetchall()}
    cursor.execute("SELECT * FROM pantry_items ORDER BY category, name")
    pantry_items = cursor.fetchall()
    conn.close()
    grouped_pantry_items = {}
    for item in pantry_items:
        category = item['category']
        if category not in grouped_pantry_items:
            grouped_pantry_items[category] = []
        grouped_pantry_items[category].append(item)
    return render_template('pantry.html', grouped_pantry_items=grouped_pantry_items, household_items=household_items, household_id=household_id, units=UNITS, statuses=STATUSES)

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
