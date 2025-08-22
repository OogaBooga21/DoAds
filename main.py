
from gmaps_scraper import get_leads_from_Maps
from web_Scrape import crawl_website
from prompt import generate_emails
import json
from openai import OpenAI
import argparse

# Load environment variables (including API key)

# Initialize OpenAI client


print("What are we looking for?")
user_input = input("Enter your query: ")
api_key = input("Enter your API key: ")
tone = input("Enter the tone for the email (default: Friendly and professional): ") or "Friendly and professional"
offer = input("Enter your collaboration offer (default: We would love to explore potential collaboration opportunities between our companies.): ") or "We would love to explore potential collaboration opportunities between our companies."
client = OpenAI(api_key=api_key)

leads = get_leads_from_Maps(user_input, max_results=5, search_for=1) #0 both, 1 only with websites, 2 only without websites

scrape_results = []
for lead in leads:
    print(f"Scraping {lead['link']} for more information...")
    scraped_info = crawl_website(lead['link'], keywords=["about", "team", "services", "careers", "contact"])

    # Check if the scraper returned any information
    if scraped_info:
        # This is the key change:
        # Create a new dictionary that includes the lead's name
        # and the scraped information.
        result_entry = {
            "name": lead['name'],
            "pages": scraped_info # The scraped data (page: text) is nested here
        }
        
        # Append the complete, structured dictionary to our results list
        scrape_results.append(result_entry)
        print(f"Found and stored information for {lead['name']}.")
    else:
        print(f"No relevant information found for {lead['name']}.")

# Define the output filename
output_filename = "scraped_results.json"
        
with open("scraped_results.json", 'w', encoding='utf-8') as json_file:
    # Use json.dump to write the list to the file
    # indent=4 makes the file human-readable (pretty-print)
    json.dump(scrape_results, json_file, indent=4)

print(f"Array has been saved to scraped_results.json")
generate_emails(client,
                tone="Friendly and professional",
                offer="We would love to explore potential collaboration opportunities between our companies.")
