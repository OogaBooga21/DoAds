import os
import re
from typing import Dict, List, Set

import pandas as pd
import requests

from importlib.resources import files
# Path to the blacklist file
BLACKLIST_FILE = "mail_blacklist.txt"


def load_blacklist() -> Set[str]:
    """Loads the blacklist domains from a text file."""
    blacklist = set()
    try:
        resource_path = files('src.resources') / BLACKLIST_FILE
        
        with open(resource_path, 'r', encoding='utf-8') as f:
            for line in f:
                domain = line.strip().lower()
                if domain:
                    blacklist.add(domain)
        return blacklist
    except FileNotFoundError:
        print(f"Error: Blacklist file '{BLACKLIST_FILE}' not found. Please create it.")
        return set()
    except Exception as e:
        print(f"An error occurred while reading the blacklist file: {e}")
        return set()


# Load the blacklist at the module level
BASE_FREE_DOMAINS = load_blacklist()


def extract_domains_from_emails(emails: List[str]) -> Dict[str, str]:
    """
    Extracts unique, non-free domains from a list of emails.
    Filters out domains that are from known free providers, including
    subdomains, country-specific TLDs, and common typos.
    """
    domain_to_email_map = {}

    # Pre-compile the regex pattern for efficiency
    if not BASE_FREE_DOMAINS:
        return {}

    free_domains_pattern = "|".join(re.escape(d) for d in BASE_FREE_DOMAINS)
    free_domains_regex = re.compile(rf".*({free_domains_pattern}).*")

    for email in emails:
        match = re.search(r"@([^@]+)", email)
        if not match:
            continue

        domain = match.group(1).lower()

        # Check if the domain contains any of the base free domains from the blacklist
        if free_domains_regex.search(domain):
            continue

        # If it's not a free domain, add it to the map
        if domain not in domain_to_email_map:
            domain_to_email_map[domain] = email

    return domain_to_email_map


def find_website_for_domain(domain: str) -> str | None:
    """
    Tries to find a valid website URL for a single domain using synchronous requests.
    Checks https/http and www/non-www variations.
    """
    patterns = [
        f"https://{domain}",
        f"https://www.{domain}",
        f"http://www.{domain}",
        f"http://{domain}",
    ]

    for url in patterns:
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                print(f"[SUCCESS] Found valid URL for {domain}: {response.url}")
                return response.url
        except requests.RequestException:
            continue

    print(f"[INFO] Could not resolve a working website for {domain}")
    return None


def find_websites_from_emails(emails: List[str]) -> List[Dict[str, str]]:
    """
    Main synchronous function to process a list of emails and find their websites.
    This is the primary function to be imported into your Flask app.

    Args:
        emails: A list of email addresses.

    Returns:
        A list of dictionaries in a format compatible with the main app workflow:
        [{'name': domain, 'link': website_url, 'email': original_email}]
    """
    domain_to_email_map = extract_domains_from_emails(emails)
    results_list = []

    if not domain_to_email_map:
        return results_list

    for domain, original_email in domain_to_email_map.items():
        print(f"-> Searching for website for domain: {domain}")
        website_url = find_website_for_domain(domain)

        if website_url:
            results_list.append(
                {"name": domain, "link": website_url, "email": original_email}
            )

    return results_list


def get_email_list_from_csv(file_path: str) -> list:
    """
    Reads a CSV file, finds a column with a case-insensitive match for
    'Email', and returns its contents as a list.
    """
    # Use pandas to handle the file object directly
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while reading CSV: {e}")
        return []

    df_columns_lower = [col.lower() for col in df.columns]
    possible_email_columns = ["email", "emails"]
    email_column = None
    for name in possible_email_columns:
        if name in df_columns_lower:
            email_column = df.columns[df_columns_lower.index(name)]
            break

    if email_column:
        email_list = df[email_column].dropna().tolist()
        return email_list
    else:
        print("Error: Could not find a column named 'Email' or 'Emails' in the file.")
        return []


# BASE_FREE_DOMAINS = load_blacklist()
# email_list = get_email_list_from_csv("/home/oli/Documents/Work/Nita/Down/Export Lista activa 5 sept.csv")
# clean_domains = find_websites_from_emails(email_list)
# print(clean_domains)
