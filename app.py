from src import create_app
import os
from dotenv import load_dotenv
import click
from redis import Redis
from rq import Queue

load_dotenv(dotenv_path='variables.env')
load_dotenv(dotenv_path='sendgrid.env')
load_dotenv(dotenv_path='brevo.env')
load_dotenv(dotenv_path='openai.env')

app = create_app()


@app.cli.command("setup-webhooks")
@click.argument("base_url")
def setup_webhooks_command(base_url):
    """Sets up the Brevo webhooks."""
    from src.utils.brevo_utils import setup_brevo_webhooks
    webhook_url = f"{base_url}/brevo-webhook"
    with app.app_context():
        setup_brevo_webhooks(webhook_url)
    print("Webhooks setup process completed.")


@app.cli.command("list-webhooks")
def list_webhooks_command():
    """Lists all configured Brevo webhooks."""
    from src.utils.brevo_utils import list_brevo_webhooks
    with app.app_context():
        list_brevo_webhooks()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
     
     