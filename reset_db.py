import os
import shutil
from app import create_app

# Path to the database file
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'mycee_stock.db')

# Remove the database file if it exists
if os.path.exists(db_path):
    os.remove(db_path)
    print("Database file removed successfully")
else:
    print("Database file not found")

# Create the app and initialize the database
app = create_app()
with app.app_context():
    from models import db
    db.create_all()
    print("Database tables created successfully")

# Now run the setup
exec(open('setup_users.py').read())