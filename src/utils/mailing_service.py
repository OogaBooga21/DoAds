from flask import current_app
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from src import db
from src.models import Email
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta

def send_email(to_address, subject, body):
    """Sends an email using the Brevo API."""
    with current_app.app_context():
        brevo_api_key = current_app.config.get('BREVO_API_KEY')
        if not brevo_api_key:
            print("BREVO_API_KEY not configured. Cannot send email.")
            return

        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = brevo_api_key

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        SENDER_EMAIL = os.environ.get('BREVO_SENDER_EMAIL')

        sender = {"name": "Daniela Gruia", "email": SENDER_EMAIL}
        to = [{"email": to_address}]

        REPLY_TO_EMAIL = os.environ.get('BREVO_REPLY_TO_EMAIL')
        REPLY_TO_NAME = os.environ.get('BREVO_REPLY_TO_NAME', 'DoAds Replies')

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sender,
            to=to,
            subject=subject,
            html_content=body,
            reply_to={"email": REPLY_TO_EMAIL, "name": REPLY_TO_NAME}
        )

        try:
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(f"Email sent to {to_address} via Brevo. Response: {api_response}")
            return api_response.message_id
        except ApiException as e:
            print(f"Exception when calling SMTPApi->send_transac_email: {e}")
            return None
        except Exception as e:
            print(f"Error sending email: {e}")
            return None



def test_mailing_service():
    """Test function to send a sample email."""
    subject = "Test Email from Mailing Service"
    body = "<strong>This is a test email sent from the mailing service.</strong>"
    send_email("moga.olimpiu21@gmail.com", subject, body)


def process_transactional_event(event_data):
    """Processes a single transactional email event from a Brevo webhook."""
    with current_app.app_context():
        message_id = event_data.get('message-id')
        event = event_data.get('event')

        if not message_id or not event:
            return

        # The webhook sends a different message_id format, we need to add < and >
        brevo_message_id = f"<{message_id}>"

        email_record = db.session.execute(
            db.select(Email).filter_by(brevo_message_id=brevo_message_id)
        ).scalar_one_or_none()

        if not email_record:
            return

        status_map = {
            'delivered': 'DELIVERED',
            'opened': 'OPENED',
            'click': 'CLICKED',
            'hardBounce': 'FAILED',
            'softBounce': 'FAILED',
            'spam': 'SPAM',
            'unsubscribed': 'UNSUBSCRIBED',
            'reply': 'REPLIED',
        }
        
        new_status = status_map.get(event)
        
        if new_status and email_record.status != new_status:
            email_record.status = new_status
            db.session.commit()

def process_inbound_email(item):
    """Processes a single inbound email from the Brevo webhook."""
    with current_app.app_context():
        in_reply_to = item.get('InReplyTo')
        if not in_reply_to:
            return

        original_email = db.session.execute(
            db.select(Email).filter_by(brevo_message_id=in_reply_to)
        ).scalar_one_or_none()

        if not original_email:
            return

        # Check if we have already processed this reply
        reply_message_id = item.get('MessageId')
        existing_reply = db.session.execute(
            db.select(Email).filter_by(brevo_message_id=reply_message_id)
        ).scalar_one_or_none()

        if existing_reply:
            return

        sent_at_str = item.get('SentAtDate')
        sent_at = None
        if sent_at_str:
            try:
                sent_at = parsedate_to_datetime(sent_at_str)
            except Exception as e:
                print(f"Could not parse date {sent_at_str}: {e}")


        # Create a new Email record for the reply
        new_reply = Email(
            lead_id=original_email.lead_id,
            previous_email_id=original_email.id,
            subject_line=item.get('Subject'),
            content=item.get('ExtractedMarkdownMessage') or item.get('RawTextBody'),
            recipient_email=original_email.sender_email, # The reply is to us
            sender_email=item['From']['Address'],
            status='RECEIVED',
            sent_at=sent_at,
            direction='INBOUND',
            brevo_message_id=reply_message_id
        )
        db.session.add(new_reply)
        original_email.status = 'REPLIED'
        db.session.commit()

