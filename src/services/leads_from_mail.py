import io
import json
import pandas as pd
from openai import OpenAI
from flask import request, send_file, redirect, url_for, current_app
from flask_login import current_user
from src import db
from src.models import Task
from src.models import Lead
import json


from src.scrapers.web_scraper import crawl_website
from src.utils.mail_utils import get_email_list_from_csv, find_websites_from_emails
from src.utils.prompt_utils import generate_emails


def leads_from_mail_service():
    # 1. Get user input and uploaded file
    api_key = current_app.config['OPENAI_API_KEY']
    tone = request.form["tone"]
    offer = request.form["offer"]
    selected_prompt = request.form["prompt_language"]
    additional_instructions = request.form["additional_instructions"]
    email_file = request.files.get("email_file")

    new_task = Task(
        user_id=current_user.id,
        language=selected_prompt,
        offer=offer,
        tone=tone,
        additional_instructions=additional_instructions,
        status='RUNNING')
    db.session.add(new_task)
    db.session.commit()

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
                    
                    combined_text = "\n\n".join(page_data["text"] for page_data in scraped_data["pages"].values())
                    new_lead = Lead(
                        task_id=new_task.id,
                        company_name=lead["name"],
                        website_url=lead["link"],
                        contact_email=scraped_data.get("email"),
                        website_content=combined_text
                    )
                    db.session.add(new_lead)
                    
                    
                    result_entry = {
                        "name": lead["name"],
                        "pages": scraped_data["pages"],
                        "email": scraped_data.get("email")
                        or lead.get("email"),  # Use email from scraper or original
                    }
                    scrape_results.append(result_entry)
            else:
                print(f"Skipping {lead['name']} because no website was found.")
                
        db.session.commit()

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
        
        json_output = emails_df.to_dict(orient="records")
        new_task.output = {"results": json_output}
        new_task.status = 'SUCCESS'
        db.session.commit()

        return redirect(url_for('main.tasks'))

    except Exception as e:
        
        new_task.status = 'FAILURE'
        new_task.output = {"error": str(e)}
        db.session.commit()
        
        return f"An error occurred: {str(e)}", 500