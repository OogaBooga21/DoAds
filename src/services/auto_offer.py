import json
from openai import OpenAI
from src import db
from src.models import Task
from src.utils.status_utils import send_status_update
from src.scrapers.web_scraper import crawl_website

def auto_offer_service(task_id, user_id, api_key, form_data):
    task = db.session.get(Task, task_id)
    if not task:
        return

    task.status = 'RUNNING'
    db.session.commit()

    try:
        url = form_data["url"]
        additional_info = form_data.get("additional_info", "")

        send_status_update(task_id, f"Scraping website: {url}")
        client = OpenAI(api_key=api_key)
        scraped_data = crawl_website(url)

        if not scraped_data or not scraped_data.get("pages"):
            raise ValueError("Could not extract meaningful content from the website.")

        send_status_update(task_id, "Website content scraped. Generating offer summary...")
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

        task.output = {"website": url, "summary": summary_text}
        task.status = 'SUCCESS'
        db.session.commit()

        send_status_update(task_id, "Task completed successfully!")
        send_status_update(task_id, "CLOSE")

    except Exception as e:
        print(f"Error in auto_offer_service for task {task_id}: {e}")
        task.status = 'FAILURE'
        task.output = {"error": str(e)}
        db.session.commit()
        send_status_update(task_id, f"An error occurred: {str(e)}")
        send_status_update(task_id, "CLOSE")
