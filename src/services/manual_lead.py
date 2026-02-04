from openai import OpenAI
from src import db
from src.models import Task, Lead
from src.utils.status_utils import send_status_update
from src.scrapers.web_scraper import crawl_website
from src.utils.prompt_utils import generate_emails
import pandas as pd

def manual_lead_service(task_id, user_id, api_key, form_data):
    task = db.session.get(Task, task_id)
    if not task:
        return

    task.status = 'RUNNING'
    db.session.commit()

    try:
        company_name = form_data["company_name"]
        contact_email = form_data["contact_email"]
        website_url = form_data["website_url"]
        offer = form_data["offer"]
        tone = form_data["tone"]
        additional_instructions = form_data["additional_instructions"]
        selected_prompt = form_data["prompt_language"]

        send_status_update(task_id, f"Scraping website for {company_name}: {website_url}")
        scraped_data = crawl_website(
            website_url, keywords=["about", "team", "services", "contact"]
        )

        if scraped_data and scraped_data.get("pages"):
            send_status_update(task_id, "Website scraped. Generating email...")
            combined_text = "\n\n".join(page_data["text"] for page_data in scraped_data["pages"].values())
            
            new_lead = Lead(
                task_id=task.id,
                company_name=company_name,
                website_url=website_url,
                contact_email=contact_email,
                website_content=combined_text
            )
            db.session.add(new_lead)
            db.session.commit()

            scrape_results = [{
                "name": company_name,
                "pages": scraped_data["pages"],
                "email": contact_email,
            }]

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
        else:
            raise ValueError("Could not scrape website.")

    except Exception as e:
        print(f"Error in manual_lead_service for task {task_id}: {e}")
        task.status = 'FAILURE'
        task.output = {"error": str(e)}
        db.session.commit()
        send_status_update(task_id, f"An error occurred: {str(e)}")
    finally:
        send_status_update(task_id, "CLOSE")

