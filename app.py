import os
import logging
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions import db, login_manager
from models import User, Category, Product, Sale, SaleItem, Expense

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-dev")

# Configure the database
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    # PythonAnywhere configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://{username}:{password}@{hostname}/{databasename}".format(
        username=os.environ.get("DB_USERNAME"),
        password=os.environ.get("DB_PASSWORD"),
        hostname=os.environ.get("DB_HOSTNAME"),
        databasename=os.environ.get("DB_NAME")
    )
else:
    # Local development configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///instance/hdfashions.db")

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)

# Import routes after extensions are initialized
from routes import *

with app.app_context():
    # Create tables
    db.create_all()

    # Create admin user if no users exist
    if User.query.count() == 0:
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            created_at=datetime.now()
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created")

if __name__ == '__main__':
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        app.run()
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
