import os
import sys
sys.path.append(os.path.dirname(__file__))

from flask import Flask
from models import db, User
from config import config

# Create app
app = Flask(__name__)
app.config.from_object(config['development'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/mycee_stock.db'

db.init_app(app)

with app.app_context():
    users = User.query.all()
    print("Current users in database:")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}, Active: {user.is_active}")