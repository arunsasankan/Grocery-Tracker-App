import sys
import os
from app import app as application

# Add the project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the environment variable for Flask app if needed
os.environ['FLASK_APP'] = 'app.py'

# Import the Flask app from app.py