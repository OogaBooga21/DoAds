import json
from src import db
from src.models import Task, Lead
from src.utils.status_utils import send_status_update
from src.scrapers.gmaps_scraper import get_leads_from_Maps

def leads_from_gmaps_no_website_service(task_id, user_id, api_key, form_data):
    task = db.session.get(Task, task_id)
    if not task:
        return

    try:
        query = form_data["query"]
        max_results = int(form_data.get("max_results", 10))

        if max_results > 100:
            max_results = 100

        send_status_update(task_id, f"Starting Google Maps search for: {query}")
        leads = get_leads_from_Maps(query, max_results=max_results, search_for=2) # Changed to search_for=2
        send_status_update(task_id, f"Found {len(leads)} potential leads without websites.")

        results = []
        for i, lead in enumerate(leads):
            phone_number = lead.get("phone", "N/A")
            send_status_update(task_id, f"({i+1}/{len(leads)}) Processing lead: {lead['name']}")
            
            new_lead = Lead(
                task_id=task.id,
                company_name=lead["name"],
                website_url=None,
                contact_email=phone_number if phone_number != "N/A" else None, # Store phone in contact_email
                website_content=f"Phone: {phone_number}" if phone_number != "N/A" else "No contact info found."
            )
            db.session.add(new_lead)
            
            results.append({
                "company_name": lead["name"],
                "phone_number": phone_number
            })
        
        db.session.commit()

        if not results:
            send_status_update(task_id, "No leads without websites found. Finishing task.")
            task.status = 'SUCCESS'
            task.output = {"results": []}
            db.session.commit()
            send_status_update(task_id, "CLOSE")
            return

        task.output = {"results": results}
        task.status = 'SUCCESS'
        db.session.commit()
        
        send_status_update(task_id, "Task completed successfully!")
        send_status_update(task_id, "CLOSE")

    except Exception as e:
        print(f"Error in leads_from_gmaps_no_website_service for task {task_id}: {e}")
        task.status = 'FAILURE'
        task.output = {"error": str(e)}
        db.session.commit()
        send_status_update(task_id, f"An error occurred: {str(e)}")
        send_status_update(task_id, "CLOSE")
