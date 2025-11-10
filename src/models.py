from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON

# Import 'db' from the application factory defined in __init__.py
from . import db

# --- 1. User Model (Authentication) ---
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(512), nullable=False)
    active = db.Column(db.Boolean, default=True)
    # api_key = db.Column(db.String(256)) # User's external OpenAI/other API key
    
    # Relationships
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    
    # Password Helper Methods
    def set_password(self, password):
        """Hashes the plain password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the stored hash against a plain password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

# --- 2. Task Model (Job Tracking) ---
class Task(db.Model):
    """Represents a job submitted by a user (Gmaps run, Mail run, etc.)"""
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Task Inputs (Data needed to run the job)
    language = db.Column(db.String(10), nullable=False)
    offer = db.Column(db.Text)
    tone = db.Column(db.String(50))
    query = db.Column(db.String(255)) 
    
    # Status and Output
    status = db.Column(db.String(50), default='PENDING', index=True) # PENDING, RUNNING, SUCCESS, FAILURE
    # JSONB is highly efficient for storing structured JSON/dictionary data in Postgres
    output = db.Column(db.JSON) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leads = db.relationship('Lead', backref='task', lazy='dynamic')
    
    def __repr__(self):
        return f'<Task {self.id} Status: {self.status}>'

# --- 3. Lead Model (Scraped Data) ---
class Lead(db.Model):
    """Represents a single business/contact found by a Task."""
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    # Lead Data
    company_name = db.Column(db.String(120))
    website_url = db.Column(db.String(255))
    contact_email = db.Column(db.String(120), index=True)
    website_content = db.Column(db.Text) # Stored combined text/summary from scraping

    # Relationships
    emails = db.relationship('Email', backref='lead', lazy='dynamic')

    def __repr__(self):
        return f'<Lead {self.company_name}>'

# --- 4. Email Model (Generated & Sent Emails) ---
class Email(db.Model):
    """Tracks a generated email, its content, and its status."""
    __tablename__ = 'emails'
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    
    # Tracking for follow-ups (Self-referential key)
    previous_email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=True) 
    
    # Email Content
    subject_line = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    
    # Status
    status = db.Column(db.String(50), default='GENERATED', index=True) # GENERATED, SENT, FAILED, OPENED, REPLIED
    sent_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships: Self-referential for follow-up chain
    follow_ups = db.relationship(
        'Email', 
        backref=db.backref('original_email', remote_side=[id]), 
        lazy='dynamic',
        foreign_keys='Email.previous_email_id' # Tells SQLAlchemy which column to use
    )

    def __repr__(self):
        return f'<Email {self.id} to {self.recipient_email}>'


# --- 5. Opt-Out Model (Blacklist) ---
class OptOut(db.Model):
    """Tracks recipients who have requested to opt-out."""
    __tablename__ = 'opt_outs'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # The user (our app's user) who sent the email
    recipient_email = db.Column(db.String(120), nullable=False, index=True)
    opt_out_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # CRITICAL: Ensures a user cannot add the same email to their blacklist twice
    __table_args__ = (
        db.UniqueConstraint('sender_id', 'recipient_email', name='_user_recipient_uc'),
    )

    def __repr__(self):
        return f'<OptOut {self.recipient_email} by User {self.sender_id}>'
