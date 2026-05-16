from app import create_app
from models import User, db

app = create_app()
with app.app_context():
    # Check Bright user details
    bright = User.query.filter_by(username='bright').first()
    print(f'Bright username: {bright.username}')
    print(f'Bright email: {bright.email}')
    print(f'Bright role: {bright.role}')
    print(f'Bright can_create_manager(): {bright.can_create_manager()}')

    # Check if the method is working correctly
    print(f'Username check: {bright.username.lower() == "bright"}')
    print(f'Email check: {"tinotenda" in bright.email.lower()}')