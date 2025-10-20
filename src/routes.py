from flask import Blueprint, render_template, request, send_file, jsonify
import io
import json
import pandas as pd
from openai import OpenAI

main_bp = Blueprint('main', __name__)

from scrapers.gmaps_scraper import get_leads_from_Maps
from scrapers.web_scraper import crawl_website # NOTE: Rename this file to web_scraper.py later
from utils.prompt_utils import generate_emails
from utils.mail_utils import get_email_list_from_csv, find_websites_from_emails

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/run', methods=['POST'])
def run_scraper():
    query = request.form["query"]
    api_key = request.form["api_key"]
    tone = request.form["tone"]
    offer = request.form["offer"]
    gmail_api_key = request.form.get("gmail_api_key")  # Use .get for optional field
    selected_prompt = request.form["prompt_language"]
    additional_instructions = request.form["additional_instructions"]

    max_results = request.form.get("max_results", 5, type=int)
    if max_results > 50:
        max_results = 50

    try:
        # 2. Get leads from Google Maps
        leads = get_leads_from_Maps(query, max_results=max_results, search_for=1)

        # 3. Scrape websites
        scrape_results = []
        for lead in leads:
            if lead.get("link") and lead["link"] != "No Website":
                print(f"Scraping website for {lead['name']}: {lead['link']}")
                scraped_data = crawl_website(
                    lead["link"], keywords=["about", "team", "services", "contact"]
                )

                if scraped_data and scraped_data.get("pages"):
                    result_entry = {
                        "name": lead["name"],
                        "pages": scraped_data["pages"],
                        "email": scraped_data.get("email"),
                    }
                    scrape_results.append(result_entry)
            else:
                print(f"Skipping {lead['name']} because no website was found.")

        # 4. Generate emails
        client = OpenAI(api_key=api_key)
        emails_df = generate_emails(
            client,
            scrape_results,
            tone,
            offer,
            prompt_filename=selected_prompt,
            additional_instructions=additional_instructions,
        )

        # 5. Return the JSON file for download
        json_buffer = io.StringIO()
        emails_df.to_json(json_buffer, orient="records", force_ascii=False, indent=2)
        json_buffer.seek(0)

        return send_file(
            io.BytesIO(json_buffer.getvalue().encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name="generated_emails.json",
        )

    except Exception as e:
        return f"An error occurred: {str(e)}"
    
@main_bp.route('/run_from_mail', methods=['POST'])
def run_from_mail():
    # 1. Get user input and uploaded file
    api_key = request.form["api_key"]
    tone = request.form["tone"]
    offer = request.form["offer"]
    selected_prompt = request.form["prompt_language"]
    additional_instructions = request.form["additional_instructions"]
    email_file = request.files.get("email_file")

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
            if lead.get("link"):
                print(f"Scraping website for {lead['name']}: {lead['link']}")
                scraped_data = crawl_website(
                    lead["link"], keywords=["about", "team", "services", "contact"]
                )

                if scraped_data and scraped_data.get("pages"):
                    result_entry = {
                        "name": lead["name"],
                        "pages": scraped_data["pages"],
                        "email": scraped_data.get("email")
                        or lead.get("email"),  # Use email from scraper or original
                    }
                    scrape_results.append(result_entry)
            else:
                print(f"Skipping {lead['name']} because no website was found.")

        # 5. Generate emails with OpenAI
        client = OpenAI(api_key=api_key)
        emails_df = generate_emails(
            client,
            scrape_results,
            tone,
            offer,
            prompt_filename=selected_prompt,
            additional_instructions=additional_instructions,
        )

        # 6. Return the JSON file for download
        json_buffer = io.StringIO()
        emails_df.to_json(json_buffer, orient="records", force_ascii=False, indent=2)
        json_buffer.seek(0)

        return send_file(
            io.BytesIO(json_buffer.getvalue().encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name="generated_emails.json",
        )

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@main_bp.route('/auto_offer', methods=['POST'])
def auto_offer():
    api_key = request.form["api_key"]
    url = request.form["url"]
    additional_info = request.form.get("additional_info", "")

    try:
        client = OpenAI(api_key=api_key)
        print(f"[INFO] Scraping website for Auto-Offer: {url}")
        scraped_data = crawl_website(url)

        if not scraped_data or not scraped_data.get("pages"):
            return {
                "error": "Could not extract meaningful content from the website."
            }, 400

        combined_text = "\n\n".join(
            [
                f"Page: {page_name}\n{page_data['text']}"
                for page_name, page_data in scraped_data["pages"].items()
            ]
        )

        prompt = f"""
DO IT IN ROMANIAN
You are a marketing strategist. Analyze the content from the website below and summarize what the company offers and how it helps its clients.
make it personal, as if the owner of the company would speak about it.
URL: {url}

{additional_info if additional_info else ''}

=== WEBSITE CONTENT ===
{combined_text}
===
Create a concise, professional offer summary in 3-5 paragraphs.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a marketing expert who writes clear, persuasive offers.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )

        summary_text = response.choices[0].message.content.strip()

        return {"website": url, "summary": summary_text}

    except Exception as e:
        return {"error": str(e)}, 500
