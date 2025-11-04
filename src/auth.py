from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from . import db
from .models import User # Import the newly created User model

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration, hashing the password and storing the API key."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # api_key = request.form.get('api_key') # User provides their key

        if not email or not password: #or not api_key:
            flash('All fields are required.')
            return redirect(url_for('auth.register'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists. Please log in.')
            return redirect(url_for('auth.login'))

        new_user = User(
            email=email, 
            # api_key=api_key,
        )
        new_user.set_password(password) # Use the hashing method

        db.session.add(new_user)
        try:
            db.session.commit()
            flash('Registration successful! You can now log in.')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('A database error occurred during registration.')
            print(f"DB Error on Register: {e}")
            return redirect(url_for('auth.register'))
        
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        # Check if user exists AND password is correct using the check_password method
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
            # Redirect to the main application page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid email or password.')
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required 
def logout():
    """Logs the user out and redirects to login."""
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))