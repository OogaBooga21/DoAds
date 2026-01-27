import io
import json
import pandas as pd
from openai import OpenAI
from src import db
from src.models import Task, Lead
from src.utils.status_utils import send_status_update
import json

from src.scrapers.gmaps_scraper import get_leads_from_Maps
from src.scrapers.web_scraper import crawl_website
from src.utils.prompt_utils import generate_emails

def leads_from_gmaps_service(task_id, user_id, api_key, form_data):
    task = db.session.get(Task, task_id)
    if not task:
        return

    try:
        query = form_data["query"]
        tone = form_data["tone"]
        offer = form_data["offer"]
        selected_prompt = form_data["prompt_language"]
        additional_instructions = form_data["additional_instructions"]
        max_results = int(form_data.get("max_results", 5))

        if max_results > 100:
            max_results = 100

        send_status_update(task_id, f"Starting Google Maps search for: {query}")
        leads = get_leads_from_Maps(query, max_results=max_results, search_for=1)
        send_status_update(task_id, f"Found {len(leads)} potential leads. Starting website scraping...")

        scrape_results = []
        for i, lead in enumerate(leads):
            if lead.get("link") and lead["link"] != "No Website":
                send_status_update(task_id, f"({i+1}/{len(leads)}) Scraping {lead['name']}'s website...")
                scraped_data = crawl_website(
                    lead["link"], keywords=["about", "team", "services", "contact"]
                )

                if scraped_data and scraped_data.get("pages"):
                    combined_text = "\n\n".join(page_data["text"] for page_data in scraped_data["pages"].values())
                    new_lead = Lead(
                        task_id=task.id,
                        company_name=lead["name"],
                        website_url=lead["link"],
                        contact_email=scraped_data.get("email"),
                        website_content=combined_text
                    )
                    db.session.add(new_lead)
                    
                    result_entry = {
                        "name": lead["name"],
                        "pages": scraped_data["pages"],
                        "email": scraped_data.get("email"),
                    }
                    scrape_results.append(result_entry)
            else:
                send_status_update(task_id, f"({i+1}/{len(leads)}) Skipping {lead['name']} (no website).")
        
        db.session.commit()

        if not scrape_results:
            send_status_update(task_id, "No websites found to scrape. Finishing task.")
            task.status = 'SUCCESS'
            task.output = {"results": []}
            db.session.commit()
            send_status_update(task_id, "CLOSE")
            return

        send_status_update(task_id, "Generating personalized emails...")
        client = OpenAI(api_key=api_key)
        emails_df = generate_emails(
            client,
            scrape_results,
            task_id, # Pass task_id here
            tone,
            offer,
            prompt_filename=selected_prompt,
            additional_instructions=additional_instructions,
        )
        
        json_output = emails_df.to_dict(orient="records")
        task.output = {"results": json_output}
        task.status = 'SUCCESS'
        db.session.commit()
        
        send_status_update(task_id, "Task completed successfully!")
        send_status_update(task_id, "CLOSE")

    except Exception as e:
        print(f"Error in leads_from_gmaps_service for task {task_id}: {e}")
        task.status = 'FAILURE'
        task.output = {"error": str(e)}
        db.session.commit()
        send_status_update(task_id, f"An error occurred: {str(e)}")
        send_status_update(task_id, "CLOSE")