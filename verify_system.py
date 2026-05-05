# System Verification Script - Mycee Accessories Stock Control

import os
import sys
import json
from pathlib import Path

class SystemVerifier:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.checks = []
        self.passed = 0
        self.failed = 0

    def check_file_exists(self, filepath, description):
        """Check if a file exists"""
        path = self.project_root / filepath
        exists = path.exists()
        status = "✓" if exists else "✗"
        self.checks.append({
            "status": status,
            "description": description,
            "passed": exists
        })
        if exists:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{status} {description}")

    def check_directory_exists(self, dirpath, description):
        """Check if a directory exists"""
        path = self.project_root / dirpath
        exists = path.is_dir()
        status = "✓" if exists else "✗"
        self.checks.append({
            "status": status,
            "description": description,
            "passed": exists
        })
        if exists:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{status} {description}")

    def check_python_module(self, module_name):
        """Check if a Python module is installed"""
        try:
            __import__(module_name)
            self.checks.append({
                "status": "✓",
                "description": f"Python module: {module_name}",
                "passed": True
            })
            self.passed += 1
            print(f"✓ Python module: {module_name}")
            return True
        except ImportError:
            self.checks.append({
                "status": "✗",
                "description": f"Python module: {module_name}",
                "passed": False
            })
            self.failed += 1
            print(f"✗ Python module: {module_name}")
            return False

    def run_verification(self):
        """Run all verification checks"""
        print("\n" + "="*60)
        print("Mycee Accessories Stock Control System - Verification")
        print("="*60 + "\n")

        print("1. Checking Project Files...")
        print("-" * 40)
        self.check_file_exists("app.py", "Main Flask application")
        self.check_file_exists("config.py", "Configuration file")
        self.check_file_exists("models.py", "Database models")
        self.check_file_exists("requirements.txt", "Dependencies list")
        self.check_file_exists("README.md", "README documentation")
        self.check_file_exists("QUICK_START.md", "Quick start guide")
        self.check_file_exists("CHANGELOG.md", "Changelog")

        print("\n2. Checking Directories...")
        print("-" * 40)
        self.check_directory_exists("templates", "Templates directory")
        self.check_directory_exists("static", "Static files directory")
        self.check_directory_exists("logs", "Logs directory (optional)")

        print("\n3. Checking Template Files...")
        print("-" * 40)
        templates = [
            "templates/base.html",
            "templates/login.html",
            "templates/register.html",
            "templates/dashboard.html",
            "templates/products.html",
            "templates/sales.html",
            "templates/reports.html",
            "templates/404.html",
            "templates/500.html",
        ]
        for template in templates:
            self.check_file_exists(template, f"Template: {Path(template).name}")

        print("\n4. Checking Static Files...")
        print("-" * 40)
        self.check_file_exists("static/style.css", "CSS stylesheet")
        self.check_file_exists("static/main.js", "JavaScript file")

        print("\n5. Checking Python Dependencies...")
        print("-" * 40)
        modules = [
            "flask",
            "flask_sqlalchemy",
            "flask_login",
            "flask_wtf",
            "wtforms",
            "werkzeug"
        ]
        installed_count = 0
        for module in modules:
            if self.check_python_module(module):
                installed_count += 1

        if installed_count < len(modules):
            print("\n⚠️  Some Python dependencies are missing.")
            print("Run: pip install -r requirements.txt")

        print("\n" + "="*60)
        print(f"Verification Summary: {self.passed} passed, {self.failed} failed")
        print("="*60 + "\n")

        if self.failed == 0:
            print("✓ All checks passed! Your system is ready to use.")
            print("\nTo start the application, run:")
            print("  Windows: python app.py or run.bat")
            print("  Linux/Mac: python3 app.py or ./run.sh")
            return True
        else:
            print("✗ Some checks failed. Please review the issues above.")
            return False

def main():
    verifier = SystemVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
