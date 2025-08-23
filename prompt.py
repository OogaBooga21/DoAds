import os
import json
import pandas as pd
from openai import OpenAI
import argparse

# Load environment variables (including API key)

# Initialize OpenAI client

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

# def process_websites(client, json_path, prompt_template, tone="Friendly and professional", offer="We would love to explore potential collaboration opportunities between our companies."):
#     """
#     Process websites from JSON and generate personalized emails
#     :param json_path: Path to JSON containing website data
#     :param prompt_template: Email generation prompt template
#     :param tone: Tone for the email (default: "Friendly and professional")
#     :param offer: Your collaboration offer (default: "We would love to explore potential collaboration opportunities between our companies.")
#     :return: DataFrame with generated emails
#     """
#     # Load website data from JSON
#     try:
#         with open(json_path, 'r', encoding="utf-8") as file:
#             websites = json.load(file)
#     except FileNotFoundError:
#         print(f"Error: {json_path} file not found.")
#         return pd.DataFrame()
#     except json.JSONDecodeError as e:
#         print(f"Error parsing JSON file: {str(e)}")
#         return pd.DataFrame()
#     except Exception as e:
#         print(f"Error loading website data: {str(e)}")
#         return pd.DataFrame()
    
#     # Prepare results storage
#     results = []
    
#     for website in websites:
#         try:
#             # Extract company name and pages
#             company_name = website['name']
#             pages = website['pages']
            
#             # Combine text from all pages
#             combined_text = "\n\n".join([f"Page: {page_name}\n{page_data['text']}" 
#                                        for page_name, page_data in pages.items()])
            
#             # Prepare prompt
#             prompt = prompt_template.replace("[PASTE WEBSITE HTML CODE HERE]", combined_text)
#             prompt = prompt.replace("[INSERT TONE HERE]", tone)
#             prompt = prompt.replace("[INSERT A SHORT DESCRIPTION OF YOUR SERVICE / OFFER]", offer)
            
#             # Generate email using OpenAI (new API)
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[
#                     {"role": "system", "content": "You are a skilled copywriter specializing in personalized cold outreach emails."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.7,
#                 max_tokens=1000
#             )
            
#             # Extract email content (new API response structure)
#             email_content = response.choices[0].message.content
            
#             # Split subject and body (assuming format: "Subject: ...\n\nBody...")
#             if "\n\n" in email_content:
#                 subject, body = email_content.split("\n\n", 1)
#                 subject = subject.replace("Subject: ", "").strip()
#             else:
#                 # Fallback if no clear separation
#                 subject = f"Collaboration Opportunity with {company_name}"
#                 body = email_content
            
#             # Store results
#             results.append({
#                 'company_name': company_name,
#                 'subject': subject,
#                 'email_body': body,
#                 'tone_used': tone,
#                 'offer_used': offer
#             })
            
#             print(f"✓ Generated email for {company_name}")
            
#         except Exception as e:
#             print(f"✗ Error processing {website.get('name', 'Unknown')}: {str(e)}")
#             results.append({
#                 'company_name': website.get('name', 'Unknown'),
#                 'subject': '',
#                 'email_body': '',
#                 'tone_used': tone,
#                 'offer_used': offer,
#                 'error': str(e)
#             })
    
#     return pd.DataFrame(results)

# def generate_emails(client, tone = "Friendly and professional", offer= "We would love to explore potential collaboration opportunities between our companies.", input_file="scraped_results.json", output_file="generated_emails.csv"):
#     # Set up command-line argument parsing

    
#     # Load prompt template
#     prompt_template = load_prompt_template()
    
#     # Process websites with specified parameters
#     results_df = process_websites(
#         client,
#         input_file,
#         prompt_template,
#         tone,
#         offer
#     )
    
#     # Save results
#     if not results_df.empty:
#         results_df.to_csv(output_file, index=False, encoding='utf-8')
#         print(f"\n✓ Generated emails saved to {output_file}")
#     else:
#         print("\n✗ No emails were generated due to errors.")

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
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a skilled copywriter specializing in personalized cold outreach emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            email_content = response.choices[0].message.content
            
            if "\n\n" in email_content:
                subject, body = email_content.split("\n\n", 1)
                subject = subject.replace("Subject: ", "").strip()
            else:
                subject = f"Collaboration Opportunity with {company_name}"
                body = email_content
            
            results.append({
                'company_name': company_name,
                'subject': subject,
                'email_body': body,
                'tone_used': tone,
                'offer_used': offer
            })
            
            print(f"✓ Generated email for {company_name}")
            
        except Exception as e:
            print(f"✗ Error processing {website.get('name', 'Unknown')}: {str(e)}")
    
    # This is also new: we RETURN the results as a DataFrame
    return pd.DataFrame(results)