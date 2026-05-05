"""Manual server entrypoint for Mycee Accessories Stock Control System."""

import os
from app import create_app

# Create the app instance for gunicorn
app = create_app(os.environ.get('FLASK_ENV') or 'production')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
