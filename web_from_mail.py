# import re
# import requests

# # Common free/public email domains to ignore
# FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com", "icloud.com"}


# def extract_domains(emails):
#     domains = set()
#     for email in emails:
#         match = re.match(r"[^@]+@([^@]+)", email)
#         if match:
#             domain = match.group(1).lower()
#             if domain not in FREE_DOMAINS:
#                 domains.add(domain)
#     return domains


# def get_websites(domains):
#     websites = {}
#     for domain in domains:
#         url = f"https://{domain}"
#         try:
#             r = requests.head(url, timeout=5, allow_redirects=True)
#             if r.status_code < 400:
#                 websites[domain] = url
#             else:
#                 websites[domain] = None
#         except requests.RequestException:
#             websites[domain] = None
#     return websites


# if __name__ == "__main__":
#     sample_emails = [
#         "alice@gmail.com",
#         "bob@acmeinc.com",
#         "carol@startup.io",
#         "dave@yahoo.com"
#     ]

#     domains = extract_domains(sample_emails)
#     websites = get_websites(domains)

#     print("Extracted Websites:")
#     for domain, site in websites.items():
#         print(domain, "->", site)


import requests
import re
from typing import List, Dict, Set

# Common free/public email domains to ignore.
FREE_DOMAINS: Set[str] = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com", "icloud.com"}

def extract_domains_from_emails(emails: List[str]) -> Dict[str, str]:
    """
    Extracts unique, non-free domains from a list of emails.
    Returns a dictionary mapping the domain to the first email found for that domain.
    """
    domain_to_email_map = {}
    for email in emails:
        match = re.search(r"@([^@]+)", email)
        if match:
            domain = match.group(1).lower()
            if domain not in FREE_DOMAINS and domain not in domain_to_email_map:
                domain_to_email_map[domain] = email
    return domain_to_email_map

def find_website_for_domain(domain: str) -> str | None:
    """
    Tries to find a valid website URL for a single domain using synchronous requests.
    Checks https/http and www/non-www variations.
    """
    # URL patterns to check in order of preference
    patterns = [
        f"https://{domain}",
        f"https://www.{domain}",
        f"http://www.{domain}",
        f"http://{domain}",
    ]
    
    for url in patterns:
        try:
            # Use a HEAD request for efficiency as we don't need the page body
            response = requests.head(url, timeout=5, allow_redirects=True)
            # Check for a successful status code (anything in the 200s or 300s)
            if response.status_code < 400:
                print(f"[SUCCESS] Found valid URL for {domain}: {response.url}")
                return response.url  # Return the final URL after any redirects
        except requests.RequestException:
            # This catches connection errors, timeouts, etc. We just try the next pattern.
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
        
        # Only add to results if a website was successfully found
        if website_url:
            results_list.append({
                "name": domain,           # Use domain as the company name
                "link": website_url,
                "email": original_email   # Include the original email
            })
            
    return results_list

# Example usage for testing the script directly
if __name__ == "__main__":
    sample_emails = [
        "contact@google.com",
        "info@un.org",
        "alice@gmail.com", # Should be filtered out
        "sales@microsoft.com",
        "bob@nonexistentdomain12345.dev", # Should not be found
        "support@corel.com" # Should resolve to www.corel.com
    ]
    
    print("--- Testing Synchronous Website Finder ---")
    results = find_websites_from_emails(sample_emails)
    
    print("\n--- Formatted Output ---")
    if results:
        for item in results:
            print(item)
    else:
        print("No websites found.")

