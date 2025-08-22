from flask import Flask, render_template, request, send_file
import os
import io
import pandas as pd

# Import your existing functions
from gmaps_scraper import get_leads_from_Maps
from web_Scrape import crawl_website
from prompt import generate_emails
from openai import OpenAI

app = Flask(__name__)

@app.route('/')
def index():
    # This will show a simple HTML form to the user
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_scraper():
    # 1. Get user input from the web form
    query = request.form['query']
    api_key = request.form['api_key']
    tone = request.form['tone']
    offer = request.form['offer']
    
    # --- This is the logic from your main.py, now in a function ---
    try:
        # 2. Get leads from Google Maps
        leads = get_leads_from_Maps(query, max_results=5, search_for=1)
        
        # 3. Scrape websites
        scrape_results = []
        for lead in leads:
            scraped_info = crawl_website(lead['link'], keywords=["about", "team", "services", "contact"])
            if scraped_info:
                result_entry = {"name": lead['name'], "pages": scraped_info}
                scrape_results.append(result_entry)

        # 4. Generate emails
        client = OpenAI(api_key=api_key)
        # You'll need to slightly modify generate_emails to accept the scrape_results directly
        # instead of reading from a file, and return a DataFrame.
        emails_df = generate_emails(client, scrape_results, tone, offer) # Modified function call
        
        # 5. Return the CSV file for download
        # Create an in-memory CSV file
        csv_buffer = io.StringIO()
        emails_df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_buffer.seek(0)
        
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='generated_emails.csv'
        )

    except Exception as e:
        # Provide feedback if something goes wrong
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    # Use os.environ.get for port, required by hosting services
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)