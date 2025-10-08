import os
import json
import pandas as pd
from openai import OpenAI
import argparse

def load_prompt_template(filename="eng_prompt.txt"):
    """Load the email generation prompt template from file with UTF-8 encoding"""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print("Error: eng_prompt.txt file not found. Please create this file with your email generation prompt.")
        exit(1)
    except Exception as e:
        print(f"Error reading prompt template: {str(e)}")
        exit(1)

def generate_emails(client, scraped_data, tone="Friendly and professional", offer="We would love to explore potential collaboration opportunities between our companies.", prompt_filename="eng_prompt.txt", additional_instructions=""):
    prompt_template = load_prompt_template(prompt_filename)
    
    # We now pass scraped_data directly instead of opening a file
    websites = scraped_data 
    
    results = []
    
    for website in websites:
        try:
            company_name = website['name']
            pages = website['pages']
            
            combined_text = "\n\n".join([f"Page: {page_name}\n{page_data['text']}" for page_name, page_data in pages.items()])
            
            prompt = prompt_template.replace("[PASTE WEBSITE HTML CODE HERE]", combined_text)
            prompt = prompt.replace("[INSERT TONE HERE]", tone)
            prompt = prompt.replace("[INSERT A SHORT DESCRIPTION OF YOUR SERVICE / OFFER]", offer)
            
                        # Append additional instructions if the user provided them
            if additional_instructions:
                prompt += f"\n\nAdditional Instructions:\n{additional_instructions}"
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a skilled copywriter specializing in personalized cold outreach emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            email_content = response.choices[0].message.content
            
            # Split the response into ranked list and email
            if '$$$$$' in email_content:
                parts = email_content.split('$$$$$', 1)
                ranked_list = parts[1].strip()
                email_text = parts[0].strip()
            else:
                ranked_list = ""
                email_text = email_content
            
            # Split email into subject and body
            if "\n\n" in email_text:
                subject, body = email_text.split("\n\n", 1)
                subject = subject.replace("Subject: ", "").strip()
            else:
                subject = f"Collaboration Opportunity with {company_name}"
                body = email_text
            
            results.append({
                'company_name': company_name,
                'contact_email': website.get('email'),
                'subject': subject,
                'email_body': body,
                'ranked_list': ranked_list  # New field for the ranked list
            })
            
            print(f"✓ Generated email for {company_name}")
            
        except Exception as e:
            print(f"✗ Error processing {website.get('name', 'Unknown')}: {str(e)}")
    
    # This is also new: we RETURN the results as a DataFrame
    return pd.DataFrame(results)