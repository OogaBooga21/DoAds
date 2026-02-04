import argparse
import json
import os
import re

import pandas as pd
from openai import OpenAI
from importlib.resources import files


def load_prompt_template(filename="eng_prompt.txt"):
    """Load the email generation prompt template from the resources file."""
    try:
        # Construct the path to the resource file within the 'resources' directory
        resource_path = files('src.resources') / filename
        
        # Open the file using the resolved path object
        with open(resource_path, "r", encoding="utf-8") as file:
            return file.read()
            
    except FileNotFoundError:
        # If the primary prompt is not found, try a generic fallback
        try:
            print(f"Warning: Prompt file '{filename}' not found. Trying 'no_website_prompt.txt'.")
            resource_path = files('src.resources') / "no_website_prompt.txt"
            with open(resource_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            print(f"Error: Neither '{filename}' nor 'no_website_prompt.txt' found in src/resources.")
            raise FileNotFoundError(f"Missing resource file: {filename}")
    except Exception as e:
        print(f"Error reading prompt template: {str(e)}")
        raise


from src.utils.status_utils import send_status_update

def generate_emails(
    client,
    scraped_data,
    task_id,
    tone="Friendly and professional",
    offer="We would love to explore potential collaboration opportunities between our companies.",
    prompt_filename="eng_prompt.txt",
    additional_instructions="",
):
    prompt_template = load_prompt_template(prompt_filename)

    # We now pass scraped_data directly instead of opening a file
    websites = scraped_data

    results = []
    total_websites = len(websites)

    for i, website in enumerate(websites):
        company_name = website.get('name', 'Unknown')
        send_status_update(task_id, f"Generating email {i+1} of {total_websites} for {company_name}...")
        try:
            company_name = website["name"]
            pages = website["pages"]

            # NEW: Structure the content for the LLM using recognized stems/keys
            page_keys = pages.keys()
            structured_content = []

            # --- 1. UNIFY CORE CONTEXT (ABOUT/DESPRE) ---
            about_text = None
            if 'about' in page_keys:
                about_text = pages['about']['text']
            elif 'despre' in page_keys:
                about_text = pages['despre']['text']
                
            if about_text:
                # Use a single, clear label for the LLM regardless of the source language
                structured_content.append(f"--- CORE CONTEXT: ABOUT/MISSION/STORY ---\n{about_text}")
                
            # --- 2. PRODUCTS/SERVICES ---
            if 'service' in page_keys:
                structured_content.append(f"--- PRODUCTS/SERVICES/OFFERS ---\n{pages['service']['text']}")
                
            # --- 3. HOMEPAGE ---
            # Include only if it hasn't been used for the 'about' context
            if 'home' in page_keys:
                structured_content.append(f"--- HOMEPAGE CONTENT (General/Backup) ---\n{pages['home']['text']}")

            processed_keys = {'about', 'despre', 'service', 'home'}
            for key, data in pages.items():
                if key not in processed_keys: 
                    structured_content.append(f"--- OTHER PAGE: {key.upper()} ---\n{data['text']}")

            combined_text = "\n\n".join(structured_content)

            prompt = prompt_template.replace(
                "[PASTE WEBSITE HTML CODE HERE]", combined_text
            )
            
            prompt = prompt.replace("[INSERT TONE HERE]", tone)
            prompt = prompt.replace(
                "[INSERT A SHORT DESCRIPTION OF YOUR SERVICE / OFFER]", offer
            )

            # Append additional instructions if the user provided them
            if additional_instructions:
                prompt += f"\n\nAdditional Instructions:\n{additional_instructions}"

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled copywriter specializing in personalized cold outreach emails.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            email_content = response.choices[0].message.content

            if "$$$$$" in email_content:
                parts = email_content.split("$$$$$", 1)
                email_part = parts[0].strip()
                remaining_part = parts[1].strip()

                # Then split remaining part by ##### to separate relevant info from activity domain
                if "#####" in remaining_part:
                    info_parts = remaining_part.split("#####", 1)
                    ranked_list = info_parts[0].strip()
                    activity_domain = info_parts[1].strip()
                else:
                    ranked_list = remaining_part
                    activity_domain = ""  # Default if not found
            else:
                # Fallback if separators are missing
                email_part = email_content
                ranked_list = ""
                activity_domain = ""

            # Split email into subject and body
            if "\n\n" in email_part:
                subject, body = email_part.split("\n\n", 1)
                subject = re.sub(r"^\s*(\*\*|)?(subject|subiect):\s*(\*\*|)?\s*", "", subject, flags=re.IGNORECASE).strip()
            else:
                subject = f"Collaboration Opportunity with {company_name}"
                body = email_part

            results.append(
                {
                    "company_name": company_name,
                    "contact_email": website.get("email"),
                    "subject": subject,
                    "email_body": body,
                    "ranked_list": ranked_list,
                    "activity_domain": activity_domain,
                }
            )

            print(f"✓ Generated email for {company_name}")

        except Exception as e:
            print(f"✗ Error processing {website.get('name', 'Unknown')}: {str(e)}")

    # This is also new: we RETURN the results as a DataFrame
    return pd.DataFrame(results)


def generate_emails_no_website(
    client,
    leads_data,
    task_id,
    tone="Friendly and professional",
    offer="We specialize in creating professional websites for businesses.",
    prompt_filename="no_website_prompt.txt",
    additional_instructions="",
):
    prompt_template = load_prompt_template(prompt_filename)
    
    results = []
    total_leads = len(leads_data)

    for i, lead in enumerate(leads_data):
        company_name = lead.get('name', 'Unknown')
        send_status_update(task_id, f"Generating email {i+1} of {total_leads} for {company_name}...")
        
        try:
            # Since there's no website, we use the company name and other details
            prompt = prompt_template.replace("[COMPANY NAME]", company_name)
            prompt = prompt.replace("[INSERT TONE HERE]", tone)
            prompt = prompt.replace("[INSERT A SHORT DESCRIPTION OF YOUR SERVICE / OFFER]", offer)

            if additional_instructions:
                prompt += f"\n\nAdditional Instructions:\n{additional_instructions}"

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skilled copywriter specializing in crafting compelling offers for businesses without a web presence.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            email_content = response.choices[0].message.content

            # Simplified parsing for "no website" emails
            if "\n\n" in email_content:
                subject, body = email_content.split("\n\n", 1)
                subject = re.sub(r"^\s*(\*\*|)?(subject|subiect):\s*(\*\*|)?\s*", "", subject, flags=re.IGNORECASE).strip()
            else:
                subject = f"A Web Presence for {company_name}"
                body = email_content

            results.append(
                {
                    "company_name": company_name,
                    "contact_email": lead.get("email"), # This will likely be None
                    "subject": subject,
                    "email_body": body,
                    "ranked_list": "N/A",
                    "activity_domain": "N/A",
                }
            )

            print(f"✓ Generated offer for {company_name}")

        except Exception as e:
            print(f"✗ Error processing {company_name}: {str(e)}")

    return pd.DataFrame(results)
