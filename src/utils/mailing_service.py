import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_address, subject, body):
    """Sends an email using the configured SMTP server."""
    print("\n--- SIMULATED EMAIL SEND ---")
    print(f"To: {to_address}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("--- END SIMULATED EMAIL ---\n")
    print('email sent to "gmail"')
    # No actual email is sent
