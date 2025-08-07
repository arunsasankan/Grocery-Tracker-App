# config.py

# IMPORTANT: This file should NOT be committed to your Git repository.
# Add it to your .gitignore file.

# Secret key for Flask sessions
SECRET_KEY = 'a_very_secret_key_for_flask_sessions' # Change this to a new random string

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_mysql_rootusername',
    'password': 'your_mysql_password',
    'database': 'grocery_db'
}