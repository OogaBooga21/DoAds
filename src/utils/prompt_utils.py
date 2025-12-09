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
        resource_path = files('src.resources') / filename
        
        # Open the file using the resolved path object
        with open(resource_path, "r", encoding="utf-8") as file:
            return file.read()
            
    except FileNotFoundError:
        # Update error message for clarity
        print(f"Error: Prompt file '{filename}' not found in src/resources.")
        # Best practice is to raise a custom exception, but for now, re-raising works
        # The original code used exit(1), which is bad in a Flask app. 
        # Raising an exception is safer.
        raise FileNotFoundError(f"Missing resource file: {filename}")
    except Exception as e:
        print(f"Error reading prompt template: {str(e)}")
        # Raise an exception instead of exit(1)
        raise


def generate_emails(
    client,
    scraped_data,
    tone="Friendly and professional",
    offer="We would love to explore potential collaboration opportunities between our companies.",
    prompt_filename="eng_prompt.txt",
    additional_instructions="",
):
    prompt_template = load_prompt_template(prompt_filename)

    # We now pass scraped_data directly instead of opening a file
    websites = scraped_data

    results = []

    for website in websites:
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
