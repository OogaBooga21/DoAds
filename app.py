from flask import Flask, render_template, request, send_file
import os
import io
import pandas as pd
import json
import io
from flask import send_file

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
    gmail_api_key = request.form['gmail_api_key']
    selected_prompt = request.form['prompt_language']
    additional_instructions = request.form['additional_instructions']
    
    max_results = request.form.get('max_results', 5, type=int)
    # Enforce a maximum of 50 results for security
    if max_results > 50:
        max_results = 50
    
    # --- This is the logic from your main.py, now in a function ---
    try:
        # 2. Get leads from Google Maps
        leads = get_leads_from_Maps(query, max_results=max_results, search_for=1)
        
        # 3. Scrape websites
        scrape_results = []
        for lead in leads:
            if lead.get('link') and lead['link'] != "No Website":
                print(f"Scraping website for {lead['name']}: {lead['link']}")
                scraped_data = crawl_website(lead['link'], keywords=["about", "team", "services", "contact"])

                # Check if the scraper returned pages
                if scraped_data and scraped_data.get('pages'):
                    result_entry = {
                        "name": lead['name'], 
                        "pages": scraped_data['pages'],
                        "email": scraped_data.get('email')  # Get the email from the scraper's result
                    }
                    scrape_results.append(result_entry)
            else:
                print(f"Skipping {lead['name']} because no website was found.")

        # 4. Generate emails
        client = OpenAI(api_key=api_key)
        # You'll need to slightly modify generate_emails to accept the scrape_results directly
        # instead of reading from a file, and return a DataFrame.
        emails_df = generate_emails(client, scrape_results, tone, offer, prompt_filename=selected_prompt, additional_instructions=additional_instructions)
        # 5. Return the CSV file for download
        # Create an in-memory CSV file
        json_buffer = io.StringIO()
        emails_df.to_json(json_buffer, orient="records", force_ascii=False, indent=2)
        json_buffer.seek(0)

        return send_file(
            io.BytesIO(json_buffer.getvalue().encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name="generated_emails.json"
        )

    except Exception as e:
        # Provide feedback if something goes wrong
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    # Use os.environ.get for port, required by hosting services
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)