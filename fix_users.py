import os
import sys
sys.path.append(os.path.dirname(__file__))

from flask import Flask
from models import db, User, StockMovement
from config import config

# Create app
app = Flask(__name__)
app.config.from_object(config['development'])
base_dir = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
db_path = os.path.join(base_dir, 'instance', 'mycee_stock.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path.replace('\\', '/')

db.init_app(app)

with app.app_context():
    # Get both users
    bright_capital = User.query.filter_by(username='Bright').first()
    bright_lower = User.query.filter_by(username='bright').first()

    if bright_capital and bright_lower:
        # Transfer stock movements from Bright to bright
        StockMovement.query.filter_by(user_id=bright_capital.id).update({'user_id': bright_lower.id})
        print('Transferred stock movements from Bright to bright')

        # Now delete Bright
        db.session.delete(bright_capital)
        db.session.commit()
        print('Removed user Bright')

    # Update 'bright' password
    if bright_lower:
        bright_lower.set_password('Ronaldo#7')
        db.session.commit()
        print('Updated bright password to Ronaldo#7')

    # List all users
    users = User.query.all()
    print('Current users:')
    for user in users:
        print(f'- {user.username}: {user.role}')