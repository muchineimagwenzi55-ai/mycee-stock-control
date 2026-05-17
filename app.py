from wtforms import SelectField
class ManagerAddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('user', 'User'), ('manager', 'Manager')], validators=[DataRequired()])
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, abort, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from dotenv import load_dotenv
import os
import io
import csv
import json
import secrets
import logging
from cryptography.fernet import Fernet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from config import config
from models import db, User, Product, StockMovement, Sale, SaleItem, UserComment, ReportTemplate

load_dotenv()

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'production'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize security extensions
    csrf = CSRFProtect(app)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    mail = Mail(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Data encryption key (generate once and store securely)
    if not os.environ.get('ENCRYPTION_KEY'):
        os.environ['ENCRYPTION_KEY'] = Fernet.generate_key().decode()
    app.config['ENCRYPTION_KEY'] = os.environ.get('ENCRYPTION_KEY')
    
    def encrypt_data(data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        f = Fernet(app.config['ENCRYPTION_KEY'].encode())
        return f.encrypt(data).decode()
    
    def decrypt_data(encrypted_data):
        """Decrypt sensitive data"""
        try:
            f = Fernet(app.config['ENCRYPTION_KEY'].encode())
            return f.decrypt(encrypted_data.encode()).decode()
        except:
            return encrypted_data  # Return as-is if decryption fails
    
    def send_admin_notification(subject, body):
        """Send notification to admin"""
        try:
            admin_email = app.config.get('ADMIN_EMAIL', 'tinotendamagwenzi10@gmail.com')
            msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[admin_email])
            msg.body = body
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send admin notification: {str(e)}")
    
    def create_default_admin():
        if not User.query.first():
            username = app.config.get('ADMIN_USERNAME', 'admin').strip().lower()
            email = app.config.get('ADMIN_EMAIL', 'admin@mycee.com').strip()
            password = app.config.get('ADMIN_PASSWORD')
            if not password:
                app.logger.warning('ADMIN_PASSWORD is not set; using default admin password. Set ADMIN_PASSWORD in production.')
                password = 'ChangeMe123!'
            existing_user = User.query.filter(func.lower(User.username) == username).first()
            if not existing_user:
                admin = User(username=username, email=email, role='admin', status='approved', is_active=True)
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()
                app.logger.info(f'Created default admin user {username} with email {email}')
        
        # Create Bright Tinotenda manager account if it doesn't exist
        bright_username = 'brighttinotenda'
        bright = User.query.filter_by(username=bright_username).first()
        if not bright:
            bright = User(
                username=bright_username,
                email='bright.tinotenda@mycee.com',
                role='manager',
                status='approved',
                is_active=True
            )
            bright.set_password('Isabel2025')
            db.session.add(bright)
            db.session.commit()
            app.logger.info(f'Created manager user {bright_username} with email bright.tinotenda@mycee.com')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        create_default_admin()
    
    # Decorators
    def admin_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_admin():
                flash('You need admin privileges to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    
    def manager_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_manager():
                flash('You need manager privileges to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    
    def approved_required(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_approved():
                flash('Your account is pending approval. Please contact an administrator.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    # ==================== Authentication Routes ====================
    @app.route('/register', methods=['GET', 'POST'])
    @limiter.limit("5 per hour")
    def register():
        user_exists = User.query.first() is not None
        registration_enabled = app.config.get('REGISTRATION_ENABLED', False) or not user_exists

        if request.method == 'POST':
            if not registration_enabled:
                flash('Registration is closed. Please ask your administrator to create your account.', 'warning')
                return redirect(url_for('login'))

            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if username:
                username = username.strip().lower()

            # Validation
            if not username or not email or not password:
                flash('All fields are required.', 'danger')
                return redirect(url_for('register'))

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('register'))

            if User.query.filter(func.lower(User.username) == username).first():
                flash('Username already exists.', 'danger')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already exists.', 'danger')
                return redirect(url_for('register'))

            # Create user with pending status
            status = 'approved' if not user_exists else 'pending'
            role = 'admin' if not user_exists else 'user'
            
            user = User(username=username, email=email, role=role, status=status)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            if status == 'pending':
                # Send admin notification
                admin_email = app.config.get('ADMIN_EMAIL', 'tinotendamagwenzi10@gmail.com')
                subject = f"New User Registration Requires Approval - {username}"
                body = f"""
A new user has registered and requires your approval:

Username: {username}
Email: {email}
Role Requested: {role}
Registration Time: {datetime.utcnow()}

Please log in to the admin panel to approve or reject this user.

Login URL: https://mycee-stock-controlgunicorn-bind-0-0-0-0.onrender.com/login
Admin Panel: https://mycee-stock-controlgunicorn-bind-0-0-0-0.onrender.com/admin/users

Thank you,
Mycee Accessories System
"""
                send_admin_notification(subject, body)
                flash('Registration successful! Your account is pending approval. You will receive an email once approved.', 'info')
            else:
                flash('Admin registration successful. Please log in.', 'success')
            
            return redirect(url_for('login'))

        return render_template('register.html', registration_enabled=registration_enabled)

        # Registration is disabled. Only managers can create users.
    
    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("10 per hour")
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data.strip().lower()
            password = form.password.data
            user = User.query.filter(func.lower(User.username) == username).first()
            if user and user.check_password(password) and user.is_active:
                if user.status == 'pending':
                    flash('Your account is pending approval. Please contact an administrator.', 'warning')
                    return redirect(url_for('login'))
                elif user.status == 'rejected':
                    flash('Your account has been rejected. Please contact an administrator.', 'danger')
                    return redirect(url_for('login'))
                else:
                    login_user(user)
                    return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    
    # ==================== Dashboard ====================
    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get statistics
        total_products = Product.query.count()
        total_stock_value = db.session.query(func.sum(Product.current_stock * Product.cost_price)).scalar() or 0
        low_stock_products = Product.query.filter(Product.current_stock <= Product.reorder_level).count()
        
        # Get today's sales
        today = datetime.utcnow().date()
        today_sales = db.session.query(func.sum(Sale.total_amount)).filter(
            func.date(Sale.created_at) == today
        ).scalar() or 0
        
        today_profit = db.session.query(func.sum(Sale.total_amount - Sale.total_cost - Sale.discount)).filter(
            func.date(Sale.created_at) == today
        ).scalar() or 0
        
        # Get recent sales
        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
        
        # Get low stock alerts
        alerts = Product.query.filter(Product.current_stock <= Product.reorder_level, Product.is_active).all()
        
        return render_template('dashboard.html',
                             total_products=total_products,
                             total_stock_value=total_stock_value,
                             low_stock_products=low_stock_products,
                             today_sales=today_sales,
                             today_profit=today_profit,
                             recent_sales=recent_sales,
                             alerts=alerts)
    
    # ==================== Product Management ====================
    @app.route('/products')
    @login_required
    def products():
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        
        query = Product.query
        if search:
            query = query.filter(
                (Product.name.ilike(f'%{search}%')) |
                (Product.sku.ilike(f'%{search}%'))
            )
        
        products = query.order_by(Product.sku).paginate(page=page, per_page=20)
        return render_template('products.html', products=products, search=search)
    
    @app.route('/product/add', methods=['GET', 'POST'])
    @manager_required
    def add_product():
        if request.method == 'POST':
            sku = request.form.get('sku')
            name = request.form.get('name')
            description = request.form.get('description')
            cost_price = request.form.get('cost_price', type=float)
            selling_price = request.form.get('selling_price', type=float)
            reorder_level = request.form.get('reorder_level', 10, type=int)
            initial_stock = request.form.get('initial_stock', 0, type=int)
            
            # Validation
            if not sku or not name or not cost_price or not selling_price:
                flash('Required fields are missing.', 'danger')
                return redirect(url_for('add_product'))
            
            if Product.query.filter_by(sku=sku).first():
                flash('SKU already exists.', 'danger')
                return redirect(url_for('add_product'))
            
            product = Product(
                sku=sku,
                name=name,
                description=description,
                cost_price=cost_price,
                selling_price=selling_price,
                reorder_level=reorder_level,
                current_stock=initial_stock
            )
            db.session.add(product)
            db.session.commit()
            
            flash(f'Product "{name}" added successfully!', 'success')
            return redirect(url_for('products'))
        
        return render_template('add_product.html')
    
    @app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
    @manager_required
    def edit_product(product_id):
        product = Product.query.get_or_404(product_id)
        
        if request.method == 'POST':
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.cost_price = request.form.get('cost_price', type=float)
            product.selling_price = request.form.get('selling_price', type=float)
            product.reorder_level = request.form.get('reorder_level', type=int)
            current_stock = request.form.get('current_stock', product.current_stock, type=int)
            product.current_stock = max(current_stock, 0)
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('products'))
        
        return render_template('edit_product.html', product=product)
    
    @app.route('/product/<int:product_id>')
    @login_required
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        
        # Get stock movements history
        page = request.args.get('page', 1, type=int)
        movements = StockMovement.query.filter_by(product_id=product.id).order_by(StockMovement.created_at.desc()).paginate(page=page, per_page=10)
        
        return render_template('product_detail.html', product=product, movements=movements)
    
    @app.route('/customized/necklaces', methods=['GET', 'POST'])
    @manager_required
    def customized_necklaces():
        if request.method == 'POST':
            base_product_id = request.form.get('base_product_id', type=int)
            name = request.form.get('name', '') or ''
            paste_names = request.form.get('paste_names', '') or ''
            quantity = request.form.get('quantity', 1, type=int)
            
            if not base_product_id or (not name.strip() and not paste_names.strip()):
                flash('Base product and at least one custom name are required.', 'danger')
                return redirect(url_for('customized_necklaces'))
            
            base_product = Product.query.get_or_404(base_product_id)
            
            import re
            def make_sku(custom_name):
                safe_name = re.sub(r'[^A-Za-z0-9]+', '-', custom_name.strip())
                safe_name = re.sub(r'-{2,}', '-', safe_name).strip('-')
                return f"{base_product.sku}-CUSTOM-{safe_name.upper()}"

            if paste_names.strip():
                names = [line.strip() for line in re.split(r'[\r\n,;]+', paste_names) if line.strip()]
                if not names:
                    flash('Please enter at least one name in the bulk paste field.', 'danger')
                    return redirect(url_for('customized_necklaces'))

                counts = {}
                for custom_name in names:
                    counts[custom_name] = counts.get(custom_name, 0) + 1

                created = 0
                updated = 0
                for custom_name, count in counts.items():
                    custom_sku = make_sku(custom_name)
                    product = Product.query.filter_by(sku=custom_sku).first()
                    if product:
                        product.current_stock += count
                        updated += 1
                    else:
                        product = Product(
                            sku=custom_sku,
                            name=f"{base_product.name} - {custom_name}",
                            description=f"Customized {base_product.name} with name: {custom_name}",
                            cost_price=base_product.cost_price,
                            selling_price=base_product.selling_price,
                            current_stock=count,
                            reorder_level=0,
                            is_active=True,
                            is_customized=True,
                            customization_type='necklace',
                            customization_details=json.dumps({'name': custom_name}),
                            base_product_id=base_product.id
                        )
                        db.session.add(product)
                        db.session.flush()
                        created += 1

                    movement = StockMovement(
                        product_id=product.id,
                        movement_type='add',
                        quantity=count,
                        reason='customization',
                        reference_number=custom_sku,
                        user_id=current_user.id,
                        notes=f'Bulk customized necklace entry for {custom_name}'
                    )
                    db.session.add(movement)

                db.session.commit()
                flash(f'Bulk custom names processed: {created} created, {updated} updated.', 'success')
                return redirect(url_for('customized_necklaces'))

            if name.strip():
                custom_name = name.strip()
                custom_sku = make_sku(custom_name)
                if Product.query.filter_by(sku=custom_sku).first():
                    flash('A customized product with this name already exists.', 'danger')
                    return redirect(url_for('customized_necklaces'))

                custom_product = Product(
                    sku=custom_sku,
                    name=f"{base_product.name} - {custom_name}",
                    description=f"Customized {base_product.name} with name: {custom_name}",
                    cost_price=base_product.cost_price,
                    selling_price=base_product.selling_price,
                    current_stock=quantity,
                    reorder_level=0,
                    is_active=True,
                    is_customized=True,
                    customization_type='necklace',
                    customization_details=json.dumps({'name': custom_name}),
                    base_product_id=base_product.id
                )
                db.session.add(custom_product)
                db.session.flush()

                movement = StockMovement(
                    product_id=custom_product.id,
                    movement_type='add',
                    quantity=quantity,
                    reason='customization',
                    reference_number=custom_sku,
                    user_id=current_user.id,
                    notes=f'Created customized necklace: {custom_name}'
                )
                movement.created_at = datetime.utcnow()
                db.session.add(movement)
                db.session.commit()

                flash(f'Customized necklace "{custom_name}" created successfully!', 'success')
                return redirect(url_for('customized_necklaces'))
        
        # Get base products (non-customized necklaces)
        base_products = Product.query.filter(
            db.and_(
                Product.is_active == True,
                Product.is_customized == False,
                Product.name.ilike('%necklace%')
            )
        ).all()
        
        selected_base_product_id = request.args.get('base_product_id', type=int)
        
        # Get customized necklaces
        customized_products = Product.query.filter(
            db.and_(
                Product.is_customized == True,
                Product.customization_type == 'necklace'
            )
        ).order_by(Product.created_at.desc()).all()
        
        return render_template(
            'customized_necklaces.html',
            base_products=base_products,
            customized_products=customized_products,
            selected_base_product_id=selected_base_product_id
        )
    
    # ==================== Stock Management ====================
    @app.route('/stock/add', methods=['GET', 'POST'])
    @manager_required
    def add_stock():
        if request.method == 'POST':
            product_id = request.form.get('product_id', type=int)
            quantity = request.form.get('quantity', type=int)
            reason = request.form.get('reason')
            reference = request.form.get('reference', '')
            notes = request.form.get('notes', '')
            
            product = Product.query.get_or_404(product_id)
            
            if quantity <= 0:
                flash('Quantity must be greater than 0.', 'danger')
                return redirect(url_for('add_stock'))
            
            # Record movement
            movement = StockMovement(
                product_id=product_id,
                movement_type='add',
                quantity=quantity,
                reason=reason,
                reference_number=reference,
                user_id=current_user.id,
                notes=notes
            )
            
            product.current_stock += quantity
            
            db.session.add(movement)
            db.session.commit()
            
            flash(f'Added {quantity} units to {product.name}. Current stock: {product.current_stock}', 'success')
            return redirect(url_for('products'))
        
        return render_template('add_stock.html')
    
    @app.route('/stock/deduct', methods=['GET', 'POST'])
    @manager_required
    def deduct_stock():
        if request.method == 'POST':
            product_id = request.form.get('product_id', type=int)
            quantity = request.form.get('quantity', type=int)
            reason = request.form.get('reason')
            reference = request.form.get('reference', '')
            notes = request.form.get('notes', '')
            
            product = Product.query.get_or_404(product_id)
            
            if quantity <= 0:
                flash('Quantity must be greater than 0.', 'danger')
                return redirect(url_for('deduct_stock'))
            
            if product.current_stock < quantity:
                flash(f'Insufficient stock. Available: {product.current_stock}', 'danger')
                return redirect(url_for('deduct_stock'))
            
            # Record movement
            movement = StockMovement(
                product_id=product_id,
                movement_type='deduct',
                quantity=quantity,
                reason=reason,
                reference_number=reference,
                user_id=current_user.id,
                notes=notes
            )
            
            product.current_stock -= quantity
            
            db.session.add(movement)
            db.session.commit()
            
            flash(f'Deducted {quantity} units from {product.name}. Current stock: {product.current_stock}', 'success')
            return redirect(url_for('products'))
        
        return render_template('deduct_stock.html')
    
    # ==================== Sales ====================
    @app.route('/sales')
    @login_required
    def sales():
        page = request.args.get('page', 1, type=int)
        date_filter = request.args.get('date')
        
        query = Sale.query
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(func.date(Sale.created_at) == filter_date)
            except:
                pass
        
        sales = query.order_by(Sale.created_at.desc()).paginate(page=page, per_page=20)
        return render_template('sales.html', sales=sales, date_filter=date_filter)
    
    @app.route('/sales/new', methods=['GET', 'POST'])
    @manager_required
    def new_sale():
        if request.method == 'POST':
            data = request.get_json()
            
            if not data.get('items') or len(data['items']) == 0:
                return jsonify({'error': 'No items in sale'}), 400
            
            sale_date_str = data.get('sale_date')
            try:
                sale_created_at = datetime.strptime(sale_date_str, '%Y-%m-%d')
            except:
                sale_created_at = datetime.utcnow()

            # Generate sale number
            sale_count = Sale.query.count() + 1
            sale_number = f"SALE-{sale_created_at.strftime('%Y%m%d')}-{sale_count:05d}"
            
            total_amount = 0
            total_cost = 0
            sale_items = []
            
            # Process items
            for item in data['items']:
                product = Product.query.get(item['product_id'])
                if not product:
                    return jsonify({'error': f'Product not found'}), 400
                
                quantity = item['quantity']
                unit_price = item['unit_price']
                subtotal = quantity * unit_price
                
                # Check stock
                if product.current_stock < quantity:
                    return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
                
                cost_total = quantity * product.cost_price
                total_amount += subtotal
                total_cost += cost_total
                
                sale_item = SaleItem(
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    cost_price=product.cost_price,
                    subtotal=subtotal
                )
                sale_items.append((sale_item, product, quantity))
            
            # Create sale
            sale = Sale(
                sale_number=sale_number,
                created_by=current_user.id,
                total_amount=total_amount,
                total_cost=total_cost,
                discount=data.get('discount', 0),
                notes=data.get('notes', ''),
                created_at=sale_created_at
            )
            
            db.session.add(sale)
            db.session.flush()  # Get the sale ID
            
            # Add sale items and update stock
            for sale_item, product, quantity in sale_items:
                sale_item.sale_id = sale.id
                db.session.add(sale_item)
                
                # Update stock
                product.current_stock -= quantity
                
                # Record movement
                movement = StockMovement(
                    product_id=product.id,
                    movement_type='deduct',
                    quantity=quantity,
                    reason='sale',
                    reference_number=sale_number,
                    user_id=current_user.id
                )
                movement.created_at = sale_created_at
                db.session.add(movement)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'sale_id': sale.id,
                'sale_number': sale_number,
                'redirect': url_for('view_sale', sale_id=sale.id)
            })
        
        products = Product.query.filter_by(is_active=True).all()
        return render_template('new_sale.html', products=products, current_date=datetime.utcnow().date().isoformat())
    
    @app.route('/sales/<int:sale_id>')
    @login_required
    def view_sale(sale_id):
        sale = Sale.query.get_or_404(sale_id)
        return render_template('view_sale.html', sale=sale)
    
    @app.route('/sales/<int:sale_id>/delete', methods=['POST'])
    @manager_required
    def delete_sale(sale_id):
        sale = Sale.query.get_or_404(sale_id)
        
        # Reverse stock movements
        for item in sale.items:
            product = item.product
            product.current_stock += item.quantity
            
            # Record the reversal movement
            movement = StockMovement(
                product_id=product.id,
                movement_type='add',
                quantity=item.quantity,
                reason='sale_reversal',
                reference_number=f"REV-{sale.sale_number}",
                user_id=current_user.id,
                notes=f"Reversal of sale {sale.sale_number}"
            )
            db.session.add(movement)
        
        # Delete the sale (cascade will delete sale items)
        db.session.delete(sale)
        db.session.commit()
        
        flash(f'Sale {sale.sale_number} has been deleted and stock restored.', 'success')
        return redirect(url_for('sales'))
    
    # ==================== Reports ====================
    @app.route('/reports')
    @login_required
    def reports():
        return render_template('reports.html')
    
    @app.route('/reports/daily', methods=['GET'])
    @login_required
    def daily_report():
        date = request.args.get('date')
        
        if date:
            try:
                report_date = datetime.strptime(date, '%Y-%m-%d').date()
            except:
                report_date = datetime.utcnow().date()
        else:
            report_date = datetime.utcnow().date()
        
        # Get sales for the day
        sales = Sale.query.filter(
            func.date(Sale.created_at) == report_date
        ).order_by(Sale.created_at.desc()).all()
        
        total_sales = sum(s.total_amount for s in sales)
        total_cost = sum(s.total_cost for s in sales)
        total_profit = total_sales - total_cost - sum(s.discount for s in sales)
        
        # Stock movements
        movements = StockMovement.query.filter(
            func.date(StockMovement.created_at) == report_date
        ).order_by(StockMovement.created_at.desc()).all()
        
        return render_template('daily_report.html',
                             report_date=report_date,
                             sales=sales,
                             total_sales=total_sales,
                             total_cost=total_cost,
                             total_profit=total_profit,
                             movements=movements)
    
    @app.route('/reports/weekly', methods=['GET'])
    @login_required
    def weekly_report():
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)
        
        custom_start = request.args.get('start_date')
        if custom_start:
            try:
                start_date = datetime.strptime(custom_start, '%Y-%m-%d').date()
            except:
                pass
        
        custom_end = request.args.get('end_date')
        if custom_end:
            try:
                end_date = datetime.strptime(custom_end, '%Y-%m-%d').date()
            except:
                pass
        
        # Get sales
        sales = Sale.query.filter(
            and_(
                func.date(Sale.created_at) >= start_date,
                func.date(Sale.created_at) <= end_date
            )
        ).all()
        
        total_sales = sum(s.total_amount for s in sales)
        total_cost = sum(s.total_cost for s in sales)
        total_profit = total_sales - total_cost - sum(s.discount for s in sales)
        
        # Daily breakdown
        daily_data = {}
        for sale in sales:
            date_key = sale.created_at.date()
            if date_key not in daily_data:
                daily_data[date_key] = {'sales': 0, 'profit': 0, 'count': 0}
            daily_data[date_key]['sales'] += sale.total_amount
            daily_data[date_key]['profit'] += sale.get_profit()
            daily_data[date_key]['count'] += 1
        
        return render_template('weekly_report.html',
                             start_date=start_date,
                             end_date=end_date,
                             total_sales=total_sales,
                             total_cost=total_cost,
                             total_profit=total_profit,
                             daily_data=daily_data)
    
    @app.route('/reports/marketing')
    @login_required
    def marketing_report():
        top_products = [
            {
                'name': row[0],
                'sku': row[1],
                'units_sold': row[2],
                'revenue': row[3] or 0,
            }
            for row in db.session.query(
                Product.name,
                Product.sku,
                func.sum(SaleItem.quantity).label('units_sold'),
                func.sum(SaleItem.subtotal).label('revenue')
            ).join(SaleItem.product).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()
        ]

        custom_sales = [
            {
                'name': row[0],
                'sku': row[1],
                'units_sold': row[2],
            }
            for row in db.session.query(
                Product.name,
                Product.sku,
                func.sum(SaleItem.quantity).label('units_sold')
            ).join(SaleItem.product).filter(Product.is_customized == True).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()
        ]

        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()

        return render_template('report_detail.html',
                               report_type='marketing',
                               title='Marketing Report',
                               description='Marketing insights from product performance and custom item demand.',
                               chart_data={
                                   'labels': [item['name'] for item in top_products],
                                   'values': [item['units_sold'] for item in top_products],
                                   'label': 'Units sold'
                               },
                               summary_items=[
                                   {'label': 'Top selling products', 'items': top_products},
                                   {'label': 'Top custom product demand', 'items': custom_sales}
                               ],
                               recent_records=recent_sales,
                               notes='Use this report to identify high-demand products, custom names with strong appeal, and marketing focus areas.')

    @app.route('/reports/procurement')
    @login_required
    def procurement_report():
        low_stock = Product.query.filter(Product.current_stock <= Product.reorder_level, Product.is_active == True).order_by(Product.current_stock.asc()).all()
        recent_purchases = StockMovement.query.filter(StockMovement.movement_type == 'add').order_by(StockMovement.created_at.desc()).limit(10).all()

        return render_template('report_detail.html',
                               report_type='procurement',
                               title='Procurement Report',
                               description='Procurement and inventory planning insights from purchases and stock levels.',
                               chart_data={
                                   'labels': [item.name for item in low_stock],
                                   'values': [item.current_stock for item in low_stock],
                                   'label': 'Stock units'
                               },
                               summary_items=[
                                   {'label': 'Low stock products', 'items': low_stock},
                                   {'label': 'Recent stock additions', 'items': recent_purchases}
                               ],
                               recent_records=recent_purchases,
                               notes='Use this report to plan purchases, replenish inventory, and manage reorder timing.')

    @app.route('/reports/finance')
    @login_required
    def finance_report():
        total_sales = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).scalar()
        total_cost = db.session.query(func.coalesce(func.sum(Sale.total_cost), 0)).scalar()
        total_discounts = db.session.query(func.coalesce(func.sum(Sale.discount), 0)).scalar()
        total_profit = total_sales - total_cost - total_discounts
        sales_count = db.session.query(func.count(Sale.id)).scalar()
        average_sale = total_sales / sales_count if sales_count else 0

        top_margin_products = [
            {
                'name': row[0],
                'sku': row[1],
                'margin': float(row[2]) if row[2] is not None else 0,
            }
            for row in db.session.query(
                Product.name,
                Product.sku,
                ((Product.selling_price - Product.cost_price) / func.nullif(Product.selling_price, 0) * 100).label('margin')
            ).filter(Product.selling_price > 0).order_by(((Product.selling_price - Product.cost_price) / Product.selling_price).desc()).limit(5).all()
        ]

        return render_template('report_detail.html',
                               report_type='finance',
                               title='Finance Report',
                               description='Key financial metrics from sales, costs, discounts, and profitability.',
                               chart_data={
                                   'labels': [item['name'] for item in top_margin_products],
                                   'values': [item['margin'] for item in top_margin_products],
                                   'label': 'Margin %'
                               },
                               finance_summary={
                                   'total_sales': total_sales,
                                   'total_cost': total_cost,
                                   'total_discounts': total_discounts,
                                   'total_profit': total_profit,
                                   'average_sale': average_sale,
                                   'sales_count': sales_count
                               },
                               summary_items=[
                                   {'label': 'Top margin products', 'items': top_margin_products}
                               ],
                               notes='Use this report to understand revenue, profitability, and discount impact for financial planning.')

    @app.route('/reports/management')
    @login_required
    def management_report():
        total_products = db.session.query(func.count(Product.id)).scalar()
        active_products = db.session.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
        total_stock = db.session.query(func.coalesce(func.sum(Product.current_stock), 0)).scalar()
        customized_count = db.session.query(func.count(Product.id)).filter(Product.is_customized == True).scalar()
        total_sales_count = db.session.query(func.count(Sale.id)).scalar()
        total_movements = db.session.query(func.count(StockMovement.id)).scalar()

        return render_template('report_detail.html',
                               report_type='management',
                               title='Management Report',
                               description='Operational and performance summary for management decisions.',
                               chart_data={
                                   'labels': ['Total products', 'Active products', 'Stock units', 'Customized products', 'Sales count', 'Movements'],
                                   'values': [total_products, active_products, total_stock, customized_count, total_sales_count, total_movements],
                                   'label': 'Management metrics'
                               },
                               management_summary={
                                   'total_products': total_products,
                                   'active_products': active_products,
                                   'total_stock': total_stock,
                                   'customized_products': customized_count,
                                   'sales_count': total_sales_count,
                                   'stock_movements': total_movements
                               },
                               notes='Use this report to track overall business health, inventory status, and operational performance.')

    @app.route('/reports/custom', methods=['GET', 'POST'])
    @manager_required
    def custom_reports():
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')

            if not name:
                flash('Report name is required.', 'danger')
                return redirect(url_for('custom_reports'))

            report = ReportTemplate(
                name=name,
                description=description,
                created_by=current_user.id
            )
            db.session.add(report)
            db.session.commit()
            flash('Custom report template created successfully.', 'success')
            return redirect(url_for('custom_reports'))

        templates = ReportTemplate.query.order_by(ReportTemplate.created_at.desc()).all()
        return render_template('custom_reports.html', templates=templates)

    @app.route('/reports/custom/<int:report_id>')
    @login_required
    def custom_report_detail(report_id):
        template = ReportTemplate.query.get_or_404(report_id)
        return render_template('custom_report_detail.html', template=template)

    def get_marketing_report_data():
        top_products = [
            {
                'name': row[0],
                'sku': row[1],
                'units_sold': row[2],
                'revenue': row[3] or 0,
            }
            for row in db.session.query(
                Product.name,
                Product.sku,
                func.sum(SaleItem.quantity).label('units_sold'),
                func.sum(SaleItem.subtotal).label('revenue')
            ).join(SaleItem.product).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()
        ]

        custom_sales = [
            {
                'name': row[0],
                'sku': row[1],
                'units_sold': row[2],
            }
            for row in db.session.query(
                Product.name,
                Product.sku,
                func.sum(SaleItem.quantity).label('units_sold')
            ).join(SaleItem.product).filter(Product.is_customized == True).group_by(Product.id).order_by(func.sum(SaleItem.quantity).desc()).limit(5).all()
        ]

        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(10).all()

        return {
            'chart_data': {
                'labels': [item['name'] for item in top_products],
                'values': [item['units_sold'] for item in top_products],
                'label': 'Units sold'
            },
            'summary_items': [
                {'label': 'Top selling products', 'items': top_products},
                {'label': 'Top custom product demand', 'items': custom_sales}
            ],
            'recent_records': recent_sales,
            'notes': 'Use this report to identify high-demand products, custom names with strong appeal, and marketing focus areas.'
        }

    def get_procurement_report_data():
        low_stock = Product.query.filter(Product.current_stock <= Product.reorder_level, Product.is_active == True).order_by(Product.current_stock.asc()).all()
        recent_purchases = StockMovement.query.filter(StockMovement.movement_type == 'add').order_by(StockMovement.created_at.desc()).limit(10).all()

        return {
            'chart_data': {
                'labels': [item.name for item in low_stock],
                'values': [item.current_stock for item in low_stock],
                'label': 'Stock units'
            },
            'summary_items': [
                {'label': 'Low stock products', 'items': low_stock},
                {'label': 'Recent stock additions', 'items': recent_purchases}
            ],
            'recent_records': recent_purchases,
            'notes': 'Use this report to plan purchases, replenish inventory, and manage reorder timing.'
        }

    def get_finance_report_data():
        total_sales = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0)).scalar()
        total_cost = db.session.query(func.coalesce(func.sum(Sale.total_cost), 0)).scalar()
        total_discounts = db.session.query(func.coalesce(func.sum(Sale.discount), 0)).scalar()
        total_profit = total_sales - total_cost - total_discounts
        sales_count = db.session.query(func.count(Sale.id)).scalar()
        average_sale = total_sales / sales_count if sales_count else 0

        top_margin_products = [
            {
                'name': row[0],
                'sku': row[1],
                'margin': float(row[2]) if row[2] is not None else 0,
            }
            for row in db.session.query(
                Product.name,
                Product.sku,
                ((Product.selling_price - Product.cost_price) / func.nullif(Product.selling_price, 0) * 100).label('margin')
            ).filter(Product.selling_price > 0).order_by(((Product.selling_price - Product.cost_price) / Product.selling_price).desc()).limit(5).all()
        ]

        return {
            'chart_data': {
                'labels': [item['name'] for item in top_margin_products],
                'values': [item['margin'] for item in top_margin_products],
                'label': 'Margin %'
            },
            'finance_summary': {
                'total_sales': total_sales,
                'total_cost': total_cost,
                'total_discounts': total_discounts,
                'total_profit': total_profit,
                'average_sale': average_sale,
                'sales_count': sales_count
            },
            'summary_items': [
                {'label': 'Top margin products', 'items': top_margin_products}
            ],
            'notes': 'Use this report to understand revenue, profitability, and discount impact for financial planning.'
        }

    def get_management_report_data():
        total_products = db.session.query(func.count(Product.id)).scalar()
        active_products = db.session.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
        total_stock = db.session.query(func.coalesce(func.sum(Product.current_stock), 0)).scalar()
        customized_count = db.session.query(func.count(Product.id)).filter(Product.is_customized == True).scalar()
        total_sales_count = db.session.query(func.count(Sale.id)).scalar()
        total_movements = db.session.query(func.count(StockMovement.id)).scalar()

        return {
            'chart_data': {
                'labels': ['Total products', 'Active products', 'Stock units', 'Customized products', 'Sales count', 'Movements'],
                'values': [total_products, active_products, total_stock, customized_count, total_sales_count, total_movements],
                'label': 'Management metrics'
            },
            'management_summary': {
                'total_products': total_products,
                'active_products': active_products,
                'total_stock': total_stock,
                'customized_products': customized_count,
                'sales_count': total_sales_count,
                'stock_movements': total_movements
            },
            'notes': 'Use this report to track overall business health, inventory status, and operational performance.'
        }

    @app.route('/reports/export/<report_type>/<format>')
    @login_required
    def export_report(report_type, export_format):
        """Export report data to CSV or PDF format"""
        if export_format not in ['csv', 'pdf']:
            abort(400)

        # Get report data based on type
        if report_type == 'marketing':
            data = get_marketing_report_data()
            title = "Marketing Report"
        elif report_type == 'procurement':
            data = get_procurement_report_data()
            title = "Procurement Report"
        elif report_type == 'finance':
            data = get_finance_report_data()
            title = "Finance Report"
        elif report_type == 'management':
            data = get_management_report_data()
            title = "Management Report"
        else:
            abort(404)

        if export_format == 'csv':
            return export_csv(data, title)
        elif export_format == 'pdf':
            return export_pdf(data, title)

    def export_csv(data, title):
        """Export data to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([title])
        writer.writerow([])

        # Write summary data if available
        if 'finance_summary' in data:
            writer.writerow(['Finance Summary'])
            writer.writerow(['Total Sales', f"${data['finance_summary']['total_sales']:.2f}"])
            writer.writerow(['Total Costs', f"${data['finance_summary']['total_cost']:.2f}"])
            writer.writerow(['Total Profit', f"${data['finance_summary']['total_profit']:.2f}"])
            writer.writerow([])

        if 'management_summary' in data:
            writer.writerow(['Management Summary'])
            writer.writerow(['Total Products', data['management_summary']['total_products']])
            writer.writerow(['Active Products', data['management_summary']['active_products']])
            writer.writerow(['Total Stock Units', data['management_summary']['total_stock']])
            writer.writerow([])

        # Write section data
        if 'summary_items' in data:
            for section in data['summary_items']:
                writer.writerow([section['label']])
                writer.writerow(['Item', 'Details'])
                for item in section['items']:
                    item_name = item.get('name') or item.get('sku') or item.get('label') or str(item)
                    details = []
                    if item.get('units_sold') is not None:
                        details.append(f"Units sold: {item['units_sold']}")
                        details.append(f"Revenue: ₦{item.get('revenue', 0):.2f}")
                    if item.get('margin') is not None:
                        details.append(f"Margin: {item['margin']:.1f}%")
                        details.append(f"SKU: {item.get('sku', '')}")
                    if item.get('current_stock') is not None:
                        details.append(f"Stock: {item['current_stock']}")
                        details.append(f"SKU: {item.get('sku', '')}")
                    if item.get('movement_type') is not None:
                        details.append(f"Qty: {item['quantity']}")
                        details.append(f"Ref: {item.get('reference_number', '-')}")
                    writer.writerow([item_name, ' | '.join(details)])
                writer.writerow([])

        # Create response
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename={title.lower().replace(" ", "_")}.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response

    def export_pdf(data, title):
        """Export data to PDF format"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))

        # Summary data
        if 'finance_summary' in data:
            elements.append(Paragraph("Finance Summary", styles['Heading2']))
            summary_data = [
                ['Total Sales', f"${data['finance_summary']['total_sales']:.2f}"],
                ['Total Costs', f"${data['finance_summary']['total_cost']:.2f}"],
                ['Total Profit', f"${data['finance_summary']['total_profit']:.2f}"]
            ]
            table = Table(summary_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

        if 'management_summary' in data:
            elements.append(Paragraph("Management Summary", styles['Heading2']))
            summary_data = [
                ['Total Products', str(data['management_summary']['total_products'])],
                ['Active Products', str(data['management_summary']['active_products'])],
                ['Total Stock Units', str(data['management_summary']['total_stock'])]
            ]
            table = Table(summary_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

        # Section data
        if 'summary_items' in data:
            for section in data['summary_items']:
                elements.append(Paragraph(section['label'], styles['Heading2']))
                section_data = [['Item', 'Details']]
                for item in section['items']:
                    item_name = item.get('name') or item.get('sku') or item.get('label') or str(item)
                    details = []
                    if item.get('units_sold') is not None:
                        details.append(f"Units sold: {item['units_sold']}")
                        details.append(f"Revenue: ₦{item.get('revenue', 0):.2f}")
                    if item.get('margin') is not None:
                        details.append(f"Margin: {item['margin']:.1f}%")
                        details.append(f"SKU: {item.get('sku', '')}")
                    if item.get('current_stock') is not None:
                        details.append(f"Stock: {item['current_stock']}")
                        details.append(f"SKU: {item.get('sku', '')}")
                    if item.get('movement_type') is not None:
                        details.append(f"Qty: {item['quantity']}")
                        details.append(f"Ref: {item.get('reference_number', '-')}")
                    section_data.append([item_name, ' | '.join(details)])

                table = Table(section_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 12))

        doc.build(elements)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename={title.lower().replace(" ", "_")}.pdf'
        response.headers['Content-Type'] = 'application/pdf'
        return response

    @app.route('/admin/reset_data', methods=['GET', 'POST'])
    @manager_required
    def reset_data():
        """Reset all system data (admin function)"""
        if request.method == 'POST':
            # Confirm reset
            confirm = request.form.get('confirm')
            if confirm != 'RESET':
                flash('Please type "RESET" to confirm data deletion.', 'danger')
                return redirect(url_for('reset_data'))

            try:
                # Delete all data in correct order (respecting foreign keys)
                SaleItem.query.delete()
                Sale.query.delete()
                StockMovement.query.delete()
                Product.query.delete()
                UserComment.query.delete()
                ReportTemplate.query.delete()

                # Reset sequences if using PostgreSQL
                db.session.execute("ALTER SEQUENCE IF EXISTS sale_sale_number_seq RESTART WITH 1;")
                db.session.execute("ALTER SEQUENCE IF EXISTS stock_movement_id_seq RESTART WITH 1;")
                db.session.execute("ALTER SEQUENCE IF EXISTS product_id_seq RESTART WITH 1;")
                db.session.execute("ALTER SEQUENCE IF EXISTS user_comment_id_seq RESTART WITH 1;")
                db.session.execute("ALTER SEQUENCE IF EXISTS report_template_id_seq RESTART WITH 1;")

                db.session.commit()
                flash('All system data has been reset successfully. The system is now ready for fresh data entry.', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error resetting data: {str(e)}', 'danger')
                return redirect(url_for('reset_data'))

        return render_template('reset_data.html')

    # ==================== Manager Functions ====================
    @app.route('/manager/add_user', methods=['GET', 'POST'])
    @manager_required
    def manager_add_user():
        if request.method == 'POST':
Email: {email}
Role: {role}

You can now log in to the system at:
https://mycee-stock-controlgunicorn-bind-0-0-0-0.onrender.com/login

Please change your password after first login for security.

Welcome to the Mycee Accessories team!

Best regards,
Mycee Accessories System
Created by: {current_user.username}
"""
                msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[email])
                msg.body = body
                mail.send(msg)
            @manager_required
            def manager_add_user():
                form = ManagerAddUserForm()
                if form.validate_on_submit():
                    username = form.username.data.strip().lower()
                    email = form.email.data
                    password = form.password.data
                    confirm_password = form.confirm_password.data
                    role = form.role.data or 'user'
                    if password != confirm_password:
                        flash('Passwords do not match.', 'danger')
                        return redirect(url_for('manager_add_user'))
                    if User.query.filter(func.lower(User.username) == username).first():
                        flash('Username already exists.', 'danger')
                        return redirect(url_for('manager_add_user'))
                    if User.query.filter_by(email=email).first():
                        flash('Email already exists.', 'danger')
                        return redirect(url_for('manager_add_user'))
                    if role == 'manager' and not current_user.can_create_manager():
                        flash('Only Bright Tinotenda can create manager accounts.', 'danger')
                        role = 'user'
                    if role not in ['user', 'manager']:
                        role = 'user'
                    user = User(username=username, email=email, role=role, status='approved', created_by=current_user.id)
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                    try:
                        subject = f"Welcome to Mycee Accessories System - Account Created"
                        body = f"""
    @login_required
    def api_search_products():
        query_text = request.args.get('q', '').strip()
        
        if not query_text:
            products = Product.query.filter_by(is_active=True).order_by(Product.sku).limit(50).all()
        else:
            products = Product.query.filter(
                db.and_(
                    Product.is_active == True,
                    db.or_(
                        Product.name.ilike(f'%{query_text}%'),
                        Product.sku.ilike(f'%{query_text}%')
                    )
                )
            ).order_by(Product.sku).limit(50).all()
        
                        msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[email])
                        msg.body = body
                        mail.send(msg)
                    except Exception as e:
                        app.logger.error(f"Failed to send welcome email: {str(e)}")
                    flash(f'User {username} created successfully as {role}. Welcome email sent.', 'success')
                    return redirect(url_for('manager_add_user'))
                return render_template('manager_add_user.html', form=form)
        product_data = []
        for product in products:
            custom_name = None
            if product.customization_details:
                try:
                    details = json.loads(product.customization_details)
                    custom_name = details.get('name')
                except Exception:
                    custom_name = None

            product_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'custom_name': custom_name,
                'customization_type': product.customization_type,
                'cost_price': product.cost_price,
                'selling_price': product.selling_price,
                'current_stock': product.current_stock,
                'reorder_level': product.reorder_level,
                'is_active': product.is_active,
                'profit_margin': round(product.get_profit_margin(), 1),
                'is_low_stock': product.is_low_stock()
            })
        
        return jsonify({'products': product_data})
    
    # ==================== Admin ====================
    @app.route('/admin/users')
    @manager_required
    def manage_users():
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status', 'all')
        
        query = User.query
        if status_filter == 'pending':
            query = query.filter_by(status='pending')
        elif status_filter == 'approved':
            query = query.filter_by(status='approved')
        elif status_filter == 'rejected':
            query = query.filter_by(status='rejected')
        
        users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
        return render_template('manage_users.html', users=users, status_filter=status_filter)
    
    @app.route('/admin/user/<int:user_id>/approve', methods=['POST'])
    @admin_required
    def approve_user(user_id):
        user = User.query.get_or_404(user_id)
        if user.status != 'pending':
            flash('User is not pending approval.', 'warning')
        else:
            user.status = 'approved'
            db.session.commit()
            
            # Send approval email to user
            try:
                subject = "Account Approved - Mycee Accessories System"
                body = f"""
Your account has been approved!

Username: {user.username}
Email: {user.email}

You can now log in to the system at:
https://mycee-stock-controlgunicorn-bind-0-0-0-0.onrender.com/login

Welcome to the Mycee Accessories team!

Best regards,
Mycee Accessories System Administrator
"""
                msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[user.email])
                msg.body = body
                mail.send(msg)
            except Exception as e:
                app.logger.error(f"Failed to send approval email: {str(e)}")
            
            flash(f'User {user.username} has been approved and notified via email.', 'success')
        
        return redirect(url_for('manage_users'))
    
    @app.route('/admin/user/<int:user_id>/reject', methods=['POST'])
    @admin_required
    def reject_user(user_id):
        user = User.query.get_or_404(user_id)
        if user.status != 'pending':
            flash('User is not pending approval.', 'warning')
        else:
            user.status = 'rejected'
            db.session.commit()
            
            # Send rejection email to user
            try:
                subject = "Account Registration - Mycee Accessories System"
                body = f"""
We regret to inform you that your account registration has been declined.

Username: {user.username}
Email: {user.email}

If you believe this is an error, please contact your system administrator.

Best regards,
Mycee Accessories System Administrator
"""
                msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[user.email])
                msg.body = body
                mail.send(msg)
            except Exception as e:
                app.logger.error(f"Failed to send rejection email: {str(e)}")
            
            flash(f'User {user.username} has been rejected and notified via email.', 'info')
        
        return redirect(url_for('manage_users'))
    
    @app.route('/admin/user/<int:user_id>/role', methods=['POST'])
    @manager_required
    def change_user_role(user_id):
        user = User.query.get_or_404(user_id)
        new_role = request.form.get('role')
        
        if new_role not in ['user', 'manager', 'admin']:
            flash('Invalid role.', 'danger')
        elif new_role == 'admin' and not current_user.is_admin():
            flash('Only administrators can assign the admin role.', 'danger')
        elif new_role == 'manager' and not current_user.can_create_manager():
            flash('Only Bright Tinotenda can create manager accounts.', 'danger')
        else:
            if user.role == 'admin' and not current_user.is_admin():
                flash('Only administrators may change admin accounts.', 'danger')
            else:
                user.role = new_role
                user.created_by = current_user.id  # Track who changed the role
                db.session.commit()
                flash(f'User {user.username} role changed to {new_role}.', 'success')
        
        return redirect(url_for('manage_users'))
    
    @app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
    @manager_required
    def toggle_user_active(user_id):
        user = User.query.get_or_404(user_id)
        if user.role == 'admin' and not current_user.is_admin():
            flash('Only administrators may change admin account status.', 'danger')
        else:
            user.is_active = not user.is_active
            db.session.commit()
            status = 'activated' if user.is_active else 'deactivated'
            flash(f'User {user.username} {status}.', 'success')
        
        return redirect(url_for('manage_users'))

    @app.route('/user/<int:user_id>/activity')
    @manager_required
    def user_activity(user_id):
        user = User.query.get_or_404(user_id)
        sales = Sale.query.filter_by(created_by=user.id).order_by(Sale.created_at.desc()).all()
        movements = StockMovement.query.filter_by(user_id=user.id).order_by(StockMovement.created_at.desc()).all()
        comments = UserComment.query.filter_by(user_id=user.id).order_by(UserComment.created_at.desc()).all()
        return render_template('user_activity.html', user=user, sales=sales, movements=movements, comments=comments)

    @app.route('/user/<int:user_id>/comment', methods=['POST'])
    @manager_required
    def add_user_comment(user_id):
        user = User.query.get_or_404(user_id)
        comment_text = request.form.get('comment', '').strip()
        if not comment_text:
            flash('Comment cannot be empty.', 'danger')
            return redirect(url_for('user_activity', user_id=user.id))
        
        comment = UserComment(user_id=user.id, author_id=current_user.id, comment=comment_text)
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully.', 'success')
        return redirect(url_for('user_activity', user_id=user.id))
    
    @app.route('/admin/backup', methods=['GET', 'POST'])
    @admin_required
    def backup_data():
        if request.method == 'POST':
            backup_type = request.form.get('backup_type')
            
            if backup_type == 'email':
                try:
                    # Generate CSV data
                    output = io.StringIO()
                    writer = csv.writer(output)
                    
                    # Products data
                    writer.writerow(['PRODUCTS'])
                    writer.writerow(['ID', 'SKU', 'Name', 'Cost Price', 'Selling Price', 'Current Stock', 'Reorder Level'])
                    products = Product.query.all()
                    for product in products:
                        writer.writerow([product.id, product.sku, product.name, product.cost_price, product.selling_price, product.current_stock, product.reorder_level])
                    
                    writer.writerow([])
                    writer.writerow(['STOCK MOVEMENTS'])
                    writer.writerow(['ID', 'Product SKU', 'Type', 'Quantity', 'User', 'Date'])
                    movements = StockMovement.query.join(Product).join(User).all()
                    for movement in movements:
                        writer.writerow([movement.id, movement.product.sku, movement.movement_type, movement.quantity, movement.user.username, movement.created_at])
                    
                    writer.writerow([])
                    writer.writerow(['SALES'])
                    writer.writerow(['ID', 'User', 'Total Amount', 'Date'])
                    sales = Sale.query.join(User).all()
                    for sale in sales:
                        writer.writerow([sale.id, sale.created_by_user.username, sale.total_amount, sale.created_at])
                    
                    # Send email
                    msg = Message('Mycee Stock Control System - Data Backup',
                                sender=app.config['MAIL_DEFAULT_SENDER'],
                                recipients=['myceeaccessories@gmail.com'])
                    msg.body = f'Data backup generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    msg.attach('backup.csv', 'text/csv', output.getvalue())
                    
                    mail.send(msg)
                    flash('Backup sent to myceeaccessories@gmail.com successfully!', 'success')
                    
                except Exception as e:
                    flash(f'Failed to send backup: {str(e)}', 'danger')
            
            return redirect(url_for('backup_data'))
        
        return render_template('backup.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        return render_template('500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
