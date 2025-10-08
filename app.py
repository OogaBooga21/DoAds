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

from web_from_mail import get_email_list_from_csv, find_websites_from_emails

app = Flask(__name__)

@app.route('/')
def index():
    # This will show a simple HTML form to the user
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_scraper():
    query = request.form['query']
    api_key = request.form['api_key']
    tone = request.form['tone']
    offer = request.form['offer']
    gmail_api_key = request.form.get('gmail_api_key')  # Use .get for optional field
    selected_prompt = request.form['prompt_language']
    additional_instructions = request.form['additional_instructions']
    
    max_results = request.form.get('max_results', 5, type=int)
    if max_results > 50:
        max_results = 50
    
    try:
        # 2. Get leads from Google Maps
        leads = get_leads_from_Maps(query, max_results=max_results, search_for=1)
        
        # 3. Scrape websites
        scrape_results = []
        for lead in leads:
            if lead.get('link') and lead['link'] != "No Website":
                print(f"Scraping website for {lead['name']}: {lead['link']}")
                scraped_data = crawl_website(lead['link'], keywords=["about", "team", "services", "contact"])

                if scraped_data and scraped_data.get('pages'):
                    result_entry = {
                        "name": lead['name'], 
                        "pages": scraped_data['pages'],
                        "email": scraped_data.get('email')
                    }
                    scrape_results.append(result_entry)
            else:
                print(f"Skipping {lead['name']} because no website was found.")

        # 4. Generate emails
        client = OpenAI(api_key=api_key)
        emails_df = generate_emails(client, scrape_results, tone, offer, prompt_filename=selected_prompt, additional_instructions=additional_instructions)
        
        # 5. Return the JSON file for download
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
        return f"An error occurred: {str(e)}"

@app.route('/run_from_mail', methods=['POST'])
def run_from_mail():
    # 1. Get user input and uploaded file
    api_key = request.form['api_key']
    tone = request.form['tone']
    offer = request.form['offer']
    selected_prompt = request.form['prompt_language']
    additional_instructions = request.form['additional_instructions']
    email_file = request.files.get('email_file')
    
    if not email_file:
        return "No file uploaded.", 400

    try:
        # 2. Read emails from the uploaded CSV
        emails = get_email_list_from_csv(email_file)

        if not emails:
            return "No emails found in the uploaded file.", 400
            
        # 3. Find websites from the emails
        leads = find_websites_from_emails(emails)
        
        # 4. Scrape websites and generate emails
        scrape_results = []
        for lead in leads:
            # We must use the link from find_websites_from_emails
            if lead.get('link'):
                print(f"Scraping website for {lead['name']}: {lead['link']}")
                scraped_data = crawl_website(lead['link'], keywords=["about", "team", "services", "contact"])

                if scraped_data and scraped_data.get('pages'):
                    result_entry = {
                        "name": lead['name'], 
                        "pages": scraped_data['pages'],
                        "email": scraped_data.get('email') or lead.get('email') # Use email from scraper or original
                    }
                    scrape_results.append(result_entry)
            else:
                print(f"Skipping {lead['name']} because no website was found.")

        # 5. Generate emails with OpenAI
        client = OpenAI(api_key=api_key)
        emails_df = generate_emails(client, scrape_results, tone, offer, prompt_filename=selected_prompt, additional_instructions=additional_instructions)
        
        # 6. Return the JSON file for download
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
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    # Use os.environ.get for port, required by hosting services
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)