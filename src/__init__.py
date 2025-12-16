from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from celery import Celery
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
celery = Celery(__name__)
migrate = Migrate()
csrf = CSRFProtect()
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite').replace("postgres://", "postgresql://", 1)


@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

def create_app(test_config=None):
    import logging
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__, instance_relative_config=True)

    db_uri = os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite').replace("postgres://", "postgresql://", 1)

    app.config.from_mapping(
        # Use environment variable for SECRET_KEY, fallback to 'dev'
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'), 
        
        # --- DATABASE CONFIGURATION ---
        SQLALCHEMY_DATABASE_URI=db_uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        # --- CELERY CONFIGURATION (Task Queue) ---
        CELERY_BROKER_URL=os.environ.get('REDIS_URL'), 
        CELERY_RESULT_BACKEND=os.environ.get('POSTGRES_URL_RESULT', db_uri),
        
        # Add a custom variable if you want to use the app's internal key for non-user tasks
        OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY'),

        # --- BREVO CONFIGURATION ---
        BREVO_API_KEY=os.environ.get('BREVO_API_KEY'),

        # --- CSRF CONFIGURATION ---
        WTF_CSRF_ENABLED=False
    )
    
    # Existing config loading logic
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Set the route to redirect to for login
    login_manager.login_message = "Please log in to access this page."
    
    # Initialize Celery
    celery.conf.update(app.config)
    
    # Import Blueprints
    from .routes import main_bp
    from .auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from . import models 

    return app