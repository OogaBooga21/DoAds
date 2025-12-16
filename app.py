from src import create_app
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='variables.env')
load_dotenv(dotenv_path='sendgrid.env')
load_dotenv(dotenv_path='brevo.env')
load_dotenv(dotenv_path='openai.env')

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
     
     