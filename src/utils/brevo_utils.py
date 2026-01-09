import os
import requests
from flask import current_app

BREVO_API_URL = "https://api.brevo.com/v3"

def get_brevo_headers():
    """Returns the headers required for Brevo API requests."""
    api_key = current_app.config.get('BREVO_API_KEY')
    if not api_key:
        raise ValueError("BREVO_API_KEY is not configured in the application.")
    return {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

def setup_brevo_webhooks(webhook_url):
    """
    Checks for and creates the necessary transactional and inbound webhooks in Brevo.
    """
    headers = get_brevo_headers()

    # 1. Check for existing webhooks
    existing_webhooks = []
    try:
        response = requests.get(f"{BREVO_API_URL}/webhooks", headers=headers)
        if response.status_code == 200:
            existing_webhooks = response.json().get('webhooks', [])
        elif response.status_code == 400 and response.json().get('code') == 'document_not_found':
            # This seems to be what Brevo returns when no webhooks exist.
            # We can safely ignore this and proceed to create the webhooks.
            print("No existing webhooks found. Proceeding to create them.")
            existing_webhooks = []
        else:
            print(f"Error fetching existing webhooks. Status code: {response.status_code}, Response: {response.text}")
            return
    except requests.RequestException as e:
        print(f"Error fetching existing webhooks: {e}")
        return
    except ValueError as e:
        print(e)
        return

    # 2. Create Transactional Webhook if it doesn't exist
    transactional_webhook_exists = any(
        wh['url'] == webhook_url and wh['type'] == 'transactional' for wh in existing_webhooks
    )
    if not transactional_webhook_exists:
        print("Creating transactional webhook...")
        payload = {
            "url": webhook_url,
            "description": f"Transactional events for {webhook_url}",
            "events": [
                "delivered", "opened", "click", 
                "hardBounce", "softBounce", "spam", "unsubscribed"
            ],
            "type": "transactional"
        }
        try:
            response = requests.post(f"{BREVO_API_URL}/webhooks", json=payload, headers=headers)
            response.raise_for_status()
            print("Transactional webhook created successfully.")
        except requests.RequestException as e:
            print(f"Error creating transactional webhook: {e}")
    else:
        print("Transactional webhook already exists.")

    # 3. Create Inbound Webhook if it doesn't exist
    inbound_webhook_exists = any(
        wh['url'] == webhook_url and wh['type'] == 'inbound' for wh in existing_webhooks
    )
    if not inbound_webhook_exists:
        print("Creating inbound webhook...")
        payload = {
            "url": webhook_url,
            "description": f"Inbound replies for {webhook_url}",
            "events": ["inboundEmailProcessed"],
            "domain": os.environ.get('BREVO_INBOUND_DOMAIN'),
            "type": "inbound"
        }
        try:
            response = requests.post(f"{BREVO_API_URL}/webhooks", json=payload, headers=headers)
            response.raise_for_status()
            print("Inbound webhook created successfully.")
        except requests.RequestException as e:
            print(f"Error creating inbound webhook: {e}")
    else:
        print("Inbound webhook already exists.")
