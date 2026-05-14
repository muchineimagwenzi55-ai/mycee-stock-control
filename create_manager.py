import os
import sys
sys.path.append(os.path.dirname(__file__))

from flask import Flask
from models import db, User
from config import config

# Create app
app = Flask(__name__)
app.config.from_object(config['production'])  # Use production config for deployed app
db.init_app(app)

with app.app_context():
    # Check if Bright Tinotenda exists
    bright_username = 'bright tinotenda'.lower().replace(' ', '')
    bright = User.query.filter_by(username=bright_username).first()

    if bright:
        print(f"User '{bright.username}' already exists with role: {bright.role}")
        if bright.role != 'manager':
            bright.role = 'manager'
            db.session.commit()
            print(f"Updated '{bright.username}' to manager role")
    else:
        # Create Bright Tinotenda as manager
        bright = User(
            username=bright_username,
            email='bright.tinotenda@mycee.com',  # Default email
            role='manager'
        )
        bright.set_password('Isabel2025')
        db.session.add(bright)
        db.session.commit()
        print(f"Created manager user '{bright.username}' with email '{bright.email}'")

    # Also ensure admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@mycee.com', role='admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'ChangeMe123!')
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin user with password from ADMIN_PASSWORD env var")

    print("\nCurrent users in database:")
    users = User.query.all()
    for user in users:
        print(f"- {user.username}: {user.role} ({user.email}) - {'Active' if user.is_active else 'Inactive'}")

    print(f"\nManager login credentials:")
    print(f"Username: {bright_username}")
    print(f"Password: Isabel2025")
    print(f"Role: manager")