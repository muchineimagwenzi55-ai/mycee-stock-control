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
    # Drop all tables
    db.drop_all()
    print("Dropped all tables")

    # Create all tables
    db.create_all()
    print("Created all tables")

    # Create default admin user
    admin = User(username='admin', email='admin@mycee.com', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("Created admin user: admin/admin123")

    # Create manager user
    manager = User(username='bright', email='bright@example.com', role='manager')
    manager.set_password('password123')
    db.session.add(manager)
    db.session.commit()
    print("Created manager user: bright/password123")

    print("Database reset complete!")