# Quick Start Guide - Mycee Accessories Stock Control System

## 🚀 Get Started in 5 Minutes

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
**Windows:**
```bash
python server.py
```
OR double-click `run.bat`

**Linux/Mac:**
```bash
python3 server.py
```

## 🌐 Deploy to Cloud (Render)

### Quick Deployment Steps

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Deploy to Render"
   git remote add origin https://github.com/yourusername/mycee-stock-control.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - New → Web Service → Connect GitHub repo
   - Configure:
     - Runtime: Python 3
     - Build: `pip install -r requirements.txt`
     - Start: `gunicorn --bind 0.0.0.0:$PORT server:app`
   - Add PostgreSQL database
   - Set env vars: `FLASK_ENV=production`, `SECRET_KEY`, `DATABASE_URL`

3. **Access Anywhere:**
   Your app will be live at `https://your-app-name.onrender.com`

### First Login
- Register as admin user
- Access from any device with internet
OR run `./run.sh`

### Step 3: Open Your Browser
Navigate to: **http://localhost:5000**

### Step 4: Create Your Account
1. Click **Register** on the login page
2. Create your admin account
3. Login with your credentials

## ✅ First Things To Do

### 1. Add Your First Product
- Go to **Products** → **Add Product**
- Enter: SKU, Name, Cost Price, Selling Price
- Click **Add Product**

### 2. Add Initial Stock
- Go to **Stock** → **Add Stock**
- Select your product
- Enter quantity
- Click **Add Stock**

### 3. Record Your First Sale
- Go to **Sales** → **New Sale**
- Select product and quantity
- Click **Add**
- Click **Complete Sale**

### 4. View Your Reports
- Go to **Reports**
- Click **Daily Report** or **Weekly Report**
- See your sales and profit data

## 📊 Dashboard Overview

**Dashboard shows you:**
- Total number of products
- Total stock value
- Number of low stock items
- Today's sales total
- Today's profit
- Recent sales list
- Low stock alerts

## 🔐 User Management

Create additional users:
1. Go to **Users** (Admin only)
2. Ask them to register
3. Change their role to Manager or User
4. They can now login

## 📱 Key Sections

| Section | What You Can Do |
|---------|-----------------|
| **Dashboard** | Overview of your business |
| **Products** | Add, edit, view all products |
| **Stock** | Add or deduct stock items |
| **Sales** | Record customer purchases |
| **Reports** | View daily/weekly analytics |
| **Users** | Manage staff accounts (Admin) |

## 💡 Pro Tips

1. **Reorder Level**: Set this low value to get alerts when stock runs out
2. **SKU**: Use unique codes like "PROD-001" for easy tracking
3. **Profit Margin**: Automatically calculated based on cost & selling price
4. **Stock History**: All movements are tracked - click product to see history
5. **Daily Reports**: Run at end of day to verify sales

## 🐛 Common Issues

**Problem**: Port 5000 already in use
- **Solution**: Change port in app.py or stop the conflicting app

**Problem**: Can't login
- **Solution**: Make sure you registered first, check username/password

**Problem**: Slow loading
- **Solution**: Clear browser cache or restart the application

## 📞 Useful Shortcuts

- **Dashboard**: http://localhost:5000/dashboard
- **Products**: http://localhost:5000/products
- **New Sale**: http://localhost:5000/sales/new
- **Reports**: http://localhost:5000/reports

## 🔒 Security Reminders

1. Change the SECRET_KEY in config.py
2. Use strong passwords
3. Don't share login credentials
4. Back up your database regularly
5. Run behind HTTPS in production

## 📖 Need More Help?

See the full **README.md** for detailed documentation on all features.

---

**Happy Selling! 📈**
