import io
import json
import pandas as pd
from openai import OpenAI
from flask import request, send_file


from scrapers.web_scraper import crawl_website
from utils.mail_utils import get_email_list_from_csv, find_websites_from_emails
from utils.prompt_utils import generate_emails


def leads_from_mail_service():
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