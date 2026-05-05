# Mycee Accessories Stock Control System

A comprehensive web-based inventory and sales management system designed for Mycee Accessories. This system helps you efficiently manage stock, track sales, monitor profit margins, and generate detailed business reports.

## Features

### 🎯 Core Features
- **Product Management**: Add, edit, and manage products with SKU, cost price, selling price
- **Stock Control**: Add and deduct stock with detailed movement tracking
- **Sales Management**: Record sales transactions with multiple items per sale
- **Daily & Weekly Reports**: Detailed business analytics and performance metrics
- **Low Stock Alerts**: Automatic notifications when inventory falls below reorder level
- **Profit Tracking**: Real-time profit and margin calculations
- **User Management**: Role-based access control (Admin, Manager, User)
- **User Authentication**: Secure login and registration system

### 📊 Dashboard
- Total products count
- Total stock value
- Low stock warnings
- Today's sales and profit
- Recent sales transactions

### 📈 Reports
- **Daily Reports**: Sales, stock movements, profit for specific days
- **Weekly Reports**: Trends, daily breakdown, average metrics
- Customizable date ranges
- Export capabilities

### 👥 User Roles
- **Admin**: Full access to all features including user management
- **Manager**: Can manage products, stocks, sales, and view reports
- **User**: Can view dashboard and reports only

## System Requirements

- Python 3.7+
- Windows, Mac, or Linux
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 100MB disk space minimum

## Installation

### Windows

1. **Download and Extract** the project to your desired location

2. **Open Command Prompt** and navigate to the project folder:
   ```
   cd path\to\Mycee Accessories Stock Control System
   ```

3. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```
   python app.py
   ```
   OR double-click `run.bat`

5. **Access the System**:
   Open your browser and go to: `http://localhost:5000`

### Linux/Mac

1. **Download and Extract** the project

2. **Open Terminal** and navigate to the project folder:
   ```
   cd path/to/Mycee\ Accessories\ Stock\ Control\ System
   ```

3. **Install Dependencies**:
   ```
   pip3 install -r requirements.txt
   ```

4. **Make Script Executable**:
   ```
   chmod +x run.sh
   ```

5. **Run the Application**:
   ```
   python3 app.py
   ```
   OR run `./run.sh`

6. **Access the System**:
   Open your browser and go to: `http://localhost:5000`

## Deployment to Render (Cloud Hosting)

To make the system accessible from any device anywhere, deploy it to Render:

### Prerequisites
- A Render account (free tier available)
- Git repository (GitHub recommended)

### Steps

1. **Push Code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/mycee-stock-control.git
   git push -u origin main
   ```

2. **Connect to Render**:
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository

3. **Configure Deployment**:
   - **Name**: mycee-stock-control
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT server:app`

4. **Add Database**:
   - In Render dashboard, click "New +" → "PostgreSQL"
   - Create a database (e.g., "mycee-db")
   - Copy the `DATABASE_URL` from database settings

5. **Set Environment Variables**:
   - In your web service settings, add:
     - `FLASK_ENV`: `production`
     - `SECRET_KEY`: Generate a secure random key
     - `DATABASE_URL`: Paste from PostgreSQL database

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Access your app at the provided URL (e.g., `https://mycee-stock-control.onrender.com`)

### Alternative: Using render.yaml

If you prefer using the render.yaml file included in the project:

1. Push the `render.yaml` file to your repository
2. In Render, choose "Blueprint" instead of "Web Service" when creating
3. Select your repository and the render.yaml will configure everything automatically

## First Time Setup

### Initial Admin Account

When you first run the system:

1. Go to the registration page
2. Create your admin account
3. After registration, the first user gets admin privileges

**Important**: Change the SECRET_KEY in `config.py` before going to production!

```python
# In config.py
SECRET_KEY = 'your-unique-secret-key-here'
```

## Usage Guide

### Dashboard
- View key metrics at a glance
- See low stock alerts
- Quick access to common actions
- View recent sales

### Adding Products

1. Click **Products** → **Add Product**
2. Enter:
   - SKU (unique product code)
   - Product name
   - Description (optional)
   - Cost price
   - Selling price
   - Reorder level (alerts when stock drops below)
3. Click **Add Product**

### Managing Stock

**Add Stock**:
1. Click **Stock** → **Add Stock**
2. Select product
3. Enter quantity
4. Choose reason (Purchase, Return, etc.)
5. Add reference number if needed
6. Click **Add Stock**

**Deduct Stock**:
1. Click **Stock** → **Deduct Stock**
2. Select product
3. Enter quantity
4. Choose reason (Damaged, Loss, Expired, etc.)
5. Add notes if needed
6. Click **Deduct Stock**

### Recording Sales

1. Click **Sales** → **New Sale**
2. Select products and quantities
3. Items are added to the sale cart
4. Apply discount if any
5. Add notes if needed
6. Click **Complete Sale**

### Viewing Reports

**Daily Report**:
1. Click **Reports** → **Daily Report**
2. Select date
3. View sales, stock movements, and profit

**Weekly Report**:
1. Click **Reports** → **Weekly Report**
2. Select date range
3. View daily breakdown and trends

### User Management (Admin Only)

1. Click **Users**
2. Change user roles (User, Manager, Admin)
3. Activate/Deactivate users
4. View user details

## Database

The system uses **SQLite** database (`mycee_stock.db`), which is:
- Stored locally in the application folder
- No separate database server needed
- Automatically created on first run
- Contains all products, sales, users, and stock movement data

### Database Tables

- `user`: User accounts and roles
- `product`: Product catalog
- `stock_movement`: Stock transaction history
- `sale`: Sales transactions
- `sale_item`: Individual items in sales

## Features in Detail

### Stock Movement Tracking

Every stock change is recorded with:
- Product name
- Quantity added/deducted
- Reason for change
- Reference number
- User who made the change
- Timestamp
- Optional notes

### Profit Calculation

- **Per Sale**: Total Amount - Total Cost - Discount
- **Profit Margin**: (Profit / Total Amount) × 100
- **Product Margin**: (Selling Price - Cost Price) / Selling Price × 100

### Low Stock Alerts

- Products showing on dashboard when below reorder level
- Red badges in product list
- Individual product detail page shows status
- Customizable reorder level per product

## Troubleshooting

### "Port 5000 already in use"
The port is already being used by another application. You can change the port by modifying `app.py`:
```python
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)  # Change port number
```

### "Database locked"
Close all other instances of the application and try again.

### "Import Error"
Make sure all dependencies are installed:
```
pip install -r requirements.txt
```

### "Login not working"
- Clear browser cache
- Check username and password spelling
- Ensure user account is active (not deactivated by admin)

## Security Notes

1. **Change Secret Key**: Update `SECRET_KEY` in `config.py` for production
2. **Use HTTPS**: Use a reverse proxy (nginx) with SSL/TLS in production
3. **Database Backup**: Regularly back up `mycee_stock.db`
4. **Strong Passwords**: Enforce strong passwords for user accounts
5. **Access Control**: Use role-based permissions appropriately

## Backing Up Your Data

To backup your data:

1. **Locate the database file**: `mycee_stock.db` in the application folder
2. **Copy the file** to a safe location
3. **Schedule regular backups** (weekly recommended)

To restore from backup:
1. Stop the application
2. Replace the current `mycee_stock.db` with your backup
3. Restart the application

## API Information

The system is built with:
- **Backend**: Flask (Python web framework)
- **Database**: SQLite
- **Frontend**: Bootstrap 5, HTML, CSS, JavaScript
- **Authentication**: Flask-Login

## System Architecture

```
Mycee Accessories Stock Control System/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── requirements.txt      # Python dependencies
├── mycee_stock.db       # SQLite database (auto-created)
├── templates/           # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── products.html
│   ├── sales.html
│   └── ...
├── static/              # CSS and JavaScript
│   ├── style.css
│   └── main.js
└── logs/               # Application logs (if enabled)
```

## Performance Tips

1. **Regular Database Maintenance**: SQLite automatically optimizes, but you can run VACUUM periodically
2. **Archive Old Data**: Move completed sales to an archive after 1 year
3. **Index Important Fields**: Consider adding database indexes for frequent searches
4. **Browser Cache**: Use browser cache for faster load times

## Support

For issues or questions:
1. Check the README
2. Review the troubleshooting section
3. Check application logs
4. Contact system administrator

## Version

**Mycee Accessories Stock Control System v1.0**
- Release Date: 2024
- Status: Production Ready

## License

This system is proprietary software for Mycee Accessories.

## Credits

Developed as a complete inventory and sales management solution.

---

**Last Updated**: 2024
**Status**: Active & Maintained
