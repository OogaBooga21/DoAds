from flask import current_app
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

def send_email(to_address, subject, body):
    """Sends an email using the Brevo API."""
    brevo_api_key = current_app.config.get('BREVO_API_KEY')
    if not brevo_api_key:
        print("BREVO_API_KEY not configured. Cannot send email.")
        return

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = brevo_api_key

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL')

    sender = {"name": "DoAds Lead Gen", "email": SENDER_EMAIL}
    to = [{"email": to_address}]

    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sender,
        to=to,
        subject=subject,
        html_content=body
    )

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"Email sent to {to_address} via Brevo. Response: {api_response}")
    except ApiException as e:
        print(f"Exception when calling SMTPApi->send_transac_email: {e}")
    except Exception as e:
        print(f"Error sending email: {e}")



def test_mailing_service():
    """Test function to send a sample email."""
    subject = "Test Email from Mailing Service"
    body = "<strong>This is a test email sent from the mailing service.</strong>"
    send_email("moga.olimpiu21@gmail.com", subject, body)
    