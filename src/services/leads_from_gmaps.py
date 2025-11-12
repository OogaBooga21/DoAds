import io
import json
import pandas as pd
from openai import OpenAI
from flask import Blueprint, render_template, request, send_file, redirect, url_for

from flask_login import current_user
from src import db
from src.models import Task
from src.models import Lead
import json

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
        
    new_task = Task(
        user_id=current_user.id,
        language=selected_prompt,
        offer=offer,
        tone=tone,
        query=query,
        additional_instructions=additional_instructions,
        status='RUNNING')
    db.session.add(new_task)
    db.session.commit()

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
                        "email": scraped_data.get("email"),
                    }
                    scrape_results.append(result_entry)
            else:
                print(f"Skipping {lead['name']} because no website was found.")
                
        db.session.commit()

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
        
        json_output = emails_df.to_dict(orient="records")
        new_task.output = json_output
        new_task.status = 'SUCCESS'
        db.session.commit()
        
        return redirect(url_for('main.tasks'))

    except Exception as e:
        
        new_task.status = 'FAILURE'
        new_task.output = {"error": str(e)}
        db.session.commit()
        
        return f"An error occurred: {str(e)}", 500