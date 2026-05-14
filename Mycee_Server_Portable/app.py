from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from dotenv import load_dotenv
import os
import io
import csv
from config import config
from models import db, User, Product, StockMovement, Sale, SaleItem

load_dotenv()

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'development'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    mail = Mail(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
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
    
    # ==================== Authentication Routes ====================
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
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
            
            # Create user
            user = User(username=username, email=email, role='user')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if username:
                username = username.strip().lower()
            
            user = User.query.filter(func.lower(User.username) == username).first()
            
            if user and user.check_password(password) and user.is_active:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        
        return render_template('login.html')
    
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
        
        products = Product.query.filter_by(is_active=True).all()
        return render_template('add_stock.html', products=products)
    
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
        
        products = Product.query.filter_by(is_active=True).all()
        return render_template('deduct_stock.html', products=products)
    
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
            
            # Generate sale number
            sale_count = Sale.query.count() + 1
            sale_number = f"SALE-{datetime.utcnow().strftime('%Y%m%d')}-{sale_count:05d}"
            
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
                notes=data.get('notes', '')
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
                db.session.add(movement)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'sale_id': sale.id,
                'sale_number': sale_number,
                'redirect': url_for('view_sale', sale_id=sale.id)
            })
        
        products = Product.query.filter_by(is_active=True).all()
        return render_template('new_sale.html', products=products)
    
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
    
    # ==================== Admin ====================
    @app.route('/admin/users')
    @admin_required
    def manage_users():
        page = request.args.get('page', 1, type=int)
        users = User.query.paginate(page=page, per_page=20)
        return render_template('manage_users.html', users=users)
    
    @app.route('/admin/user/<int:user_id>/role', methods=['POST'])
    @admin_required
    def change_user_role(user_id):
        user = User.query.get_or_404(user_id)
        new_role = request.form.get('role')
        
        if new_role in ['user', 'manager', 'admin']:
            user.role = new_role
            db.session.commit()
            flash(f'User {user.username} role changed to {new_role}.', 'success')
        else:
            flash('Invalid role.', 'danger')
        
        return redirect(url_for('manage_users'))
    
    @app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
    @admin_required
    def toggle_user_active(user_id):
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.username} {status}.', 'success')
        
        return redirect(url_for('manage_users'))
    
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
