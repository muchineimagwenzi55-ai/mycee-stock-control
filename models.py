from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    status = db.Column(db.String(20), default='approved')  # pending, approved, rejected
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Who created this user
    email_verification_token = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales = db.relationship('Sale', backref='created_by_user', lazy=True, foreign_keys='Sale.created_by')
    stock_movements = db.relationship('StockMovement', backref='user', lazy=True)
    comments = db.relationship('UserComment', foreign_keys='UserComment.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    created_users = db.relationship('User', backref=db.backref('creator', remote_side=[id]), lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role in ['admin', 'manager']
    
    def is_approved(self):
        return self.status == 'approved' and self.is_active
    
    def can_create_manager(self):
        """Only Bright Tinotenda (manager) can create other managers"""
        return self.username.lower() == 'bright' and 'tinotenda' in self.email.lower() and self.is_manager()
    
    def can_approve_users(self):
        """Only admin can approve users"""
        return self.is_admin()

class Product(db.Model):
    """Product model"""
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    cost_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    current_stock = db.Column(db.Integer, default=0)
    reorder_level = db.Column(db.Integer, default=10)  # Trigger low stock alert
    is_active = db.Column(db.Boolean, default=True)
    is_customized = db.Column(db.Boolean, default=False)
    customization_type = db.Column(db.String(50))  # necklace, bracelet, cuban
    customization_details = db.Column(db.Text)  # JSON string for details like name
    base_product_id = db.Column(db.Integer, db.ForeignKey('product.id'))  # Reference to base product if customized
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True, cascade='all, delete-orphan')
    sales_items = db.relationship('SaleItem', backref='product', lazy=True, cascade='all, delete-orphan')
    base_product = db.relationship('Product', remote_side=[id], backref='customized_products')
    
    def get_profit_margin(self):
        """Calculate profit margin percentage"""
        if self.selling_price == 0:
            return 0
        return ((self.selling_price - self.cost_price) / self.selling_price) * 100
    
    def is_low_stock(self):
        """Check if product is below reorder level"""
        return self.current_stock <= self.reorder_level

class StockMovement(db.Model):
    """Track all stock additions and deductions"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # 'add', 'deduct', 'return'
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)  # 'purchase', 'sale', 'damaged', 'inventory_adjustment', etc.
    reference_number = db.Column(db.String(100))  # e.g., invoice number, sale ID
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<StockMovement {self.product.sku} {self.movement_type} {self.quantity}>'

class Sale(db.Model):
    """Sales records"""
    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    
    def get_profit(self):
        """Calculate profit from this sale"""
        return self.total_amount - self.total_cost - self.discount
    
    def get_profit_margin(self):
        """Calculate profit margin percentage"""
        if self.total_amount == 0:
            return 0
        return (self.get_profit() / self.total_amount) * 100

class SaleItem(db.Model):
    """Individual items in a sale"""
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f'<SaleItem {self.product.name} x{self.quantity}>'

class ReportTemplate(db.Model):
    """Custom report definitions created by users"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship('User', foreign_keys=[created_by], backref='report_templates')

    def __repr__(self):
        return f'<ReportTemplate {self.name}>'

class UserComment(db.Model):
    """Comments or corrections left on user accounts"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    author = db.relationship('User', foreign_keys=[author_id], backref='authored_comments')

    def __repr__(self):
        return f'<UserComment user_id={self.user_id} author_id={self.author_id}>'
