import io
import json
import pandas as pd
from openai import OpenAI
from flask import Blueprint, render_template, request, send_file

from src.scrapers.gmaps_scraper import get_leads_from_Maps
from src.scrapers.web_scraper import crawl_website
from src.utils.prompt_utils import generate_emails

def leads_from_gmaps_service():
    query = request.form["query"]
    api_key = request.form["api_key"]
    tone = request.form["tone"]
    offer = request.form["offer"]
    gmail_api_key = request.form.get("gmail_api_key")  #.get for optional field
    selected_prompt = request.form["prompt_language"]
    additional_instructions = request.form["additional_instructions"]

    max_results = request.form.get("max_results", 5, type=int)
    if max_results > 50:
        max_results = 50

    try:
        # Google Maps
        leads = get_leads_from_Maps(query, max_results=max_results, search_for=1)

        # Scrape
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

        # Generate
        client = OpenAI(api_key=api_key)
        emails_df = generate_emails(
            client,
            scrape_results,
            tone,
            offer,
            prompt_filename=selected_prompt,
            additional_instructions=additional_instructions,
        )

        # Return
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