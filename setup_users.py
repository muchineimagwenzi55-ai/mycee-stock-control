import os
import sys
sys.path.append(os.path.dirname(__file__))

from flask import Flask
from models import db, User
from config import config

# Create app
app = Flask(__name__)
app.config.from_object(config['development'])
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'mycee_stock.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

db.init_app(app)

with app.app_context():
    # Check if bright exists
    bright = User.query.filter_by(username='bright').first()
    if bright:
        print(f"User 'bright' exists with role: {bright.role}")
        if bright.role != 'manager':
            bright.role = 'manager'
            db.session.commit()
            print("Updated 'bright' to manager role")
    else:
        # Create bright as manager
        bright = User(username='bright', email='bright.tinotenda@mycee.com', role='manager')
        bright.set_password('password123')  # Default password
        db.session.add(bright)
        db.session.commit()
        print("Created user 'bright' with manager role")

    # Also create an admin user if needed
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@mycee.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created admin user")

    print("Users in database:")
    users = User.query.all()
    for user in users:
        print(f"- {user.username}: {user.role}")