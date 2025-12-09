from flask import request, redirect, url_for
from flask_login import current_user
from openai import OpenAI
from src import db
from src.models import Task, Lead
from src.scrapers.web_scraper import crawl_website
from src.utils.prompt_utils import generate_emails
import pandas as pd

def manual_lead_service():
    company_name = request.form["company_name"]
    contact_email = request.form["contact_email"]
    website_url = request.form["website_url"]
    offer = request.form["offer"]
    tone = request.form["tone"]
    additional_instructions = request.form["additional_instructions"]
    selected_prompt = request.form["prompt_language"]
    api_key = request.form["api_key"]

    new_task = Task(
        user_id=current_user.id,
        language=selected_prompt,
        offer=offer,
        tone=tone,
        additional_instructions=additional_instructions,
        status='RUNNING'
    )
    db.session.add(new_task)
    db.session.commit()

    try:
        print(f"Scraping website for {company_name}: {website_url}")
        scraped_data = crawl_website(
            website_url, keywords=["about", "team", "services", "contact"]
        )

        if scraped_data and scraped_data.get("pages"):
            combined_text = "\n\n".join(page_data["text"] for page_data in scraped_data["pages"].values())
            
            new_lead = Lead(
                task_id=new_task.id,
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
                tone,
                offer,
                prompt_filename=selected_prompt,
                additional_instructions=additional_instructions,
            )
            
            json_output = emails_df.to_dict(orient="records")
            new_task.output = {"results": json_output}
            new_task.status = 'SUCCESS'
            db.session.commit()
        else:
            new_task.status = 'FAILURE'
            new_task.output = {"error": "Could not scrape website."}
            db.session.commit()

        return redirect(url_for('main.tasks'))

    except Exception as e:
        new_task.status = 'FAILURE'
        new_task.output = {"error": str(e)}
        db.session.commit()
        return f"An error occurred: {str(e)}", 500
