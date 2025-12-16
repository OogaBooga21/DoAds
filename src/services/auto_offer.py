import json
import pandas as pd
from openai import OpenAI
from flask import request, current_app

from src.scrapers.web_scraper import crawl_website


def auto_offer_service():
    api_key = current_app.config['OPENAI_API_KEY']
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
