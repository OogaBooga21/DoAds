import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin, urlparse
import tldextract
import re

def is_valid_internal_link(base_url, link):
    if not link:
        return False
    if link.startswith('#') or link.startswith('mailto:') or link.startswith('tel:'):
        return False
    parsed_link = urlparse(urljoin(base_url, link))
    base_domain = tldextract.extract(base_url).domain
    link_domain = tldextract.extract(parsed_link.netloc).domain
    return base_domain == link_domain

def get_readable_text(url):
    print(f"  -> Scraping full text from: {url}")
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    doc = Document(resp.text)
    soup = BeautifulSoup(doc.summary(), 'html.parser')
    return soup.get_text(separator='\n', strip=True)

# def crawl_website(start_url, keywords=None, max_pages=10):
#     if keywords is None:
#         keywords = ["about", "team", "services", "careers", "contact", "servicii","despre","despre-noi","despre-mine", "echipa", "cariera", "contacte","oferte","produse","produse","preturi"]
    
#     found_pages = {}
    
#     # --- Part 1: Scrape and SUMMARIZE the Home Page using Transformers ---
#     print(f"Scraping and summarizing home page: {start_url}")
#     try:
#         resp = requests.get(start_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
#         resp.raise_for_status()
#     except requests.RequestException as e:
#         print(f"Fatal: Could not fetch the start_url. Exiting. Error: {e}")
#         return {}

#     soup = BeautifulSoup(resp.text, 'html.parser')
    
#     # --- Clean and save the full readable text of the home page ---
#     doc = Document(resp.text)
#     cleaned_html = doc.summary()
#     soup = BeautifulSoup(cleaned_html, 'html.parser')
#     home_page_text = soup.get_text(separator='\n', strip=True)

#     if home_page_text:
#         found_pages["home"] = {
#             "url": start_url,
#             "text": home_page_text
#         }
    
#     # --- Part 2: Find links and get full content for other pages ---
#     candidate_links = set()
#     full_soup = BeautifulSoup(resp.text, 'html.parser')
#     for link in full_soup.find_all("a", href=True):
#         href = urljoin(start_url, link['href'])
#         if is_valid_internal_link(start_url, href) and href != start_url:
#             candidate_links.add(href)

#     for url in candidate_links:
#         if len(found_pages) >= max_pages:
#             print("Reached max pages limit.")
#             break
        
#         for keyword in keywords:
#             if keyword in url.lower():
#                 if keyword not in found_pages:
#                     content = get_readable_text(url)
#                     if content:
#                         found_pages[keyword] = {
#                             "url": url,
#                             "text": content
#                         }
#                 break 

#     return found_pages

def crawl_website(start_url, keywords=None, max_pages=10):
    """
    Crawls a website, extracts text from relevant pages, and finds the first email address.
    """
    if keywords is None:
        keywords = ["about", "team", "services", "careers", "contact", "servicii","despre","despre-noi","despre-mine", "echipa", "cariera", "contacte","oferte","produse","produse","preturi"]
    
    found_pages = {}
    all_emails = set() # Use a set to store unique emails

    print(f"Scraping home page: {start_url}")
    try:
        resp = requests.get(start_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        initial_html = resp.text
    except requests.RequestException as e:
        print(f"Fatal: Could not fetch the start_url. Exiting. Error: {e}")
        # Return a dictionary with the expected structure, but empty
        return {"pages": {}, "email": None}

    # --- Part 1: Find emails on the home page and get its content ---
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails_on_home = re.findall(email_regex, initial_html)
    all_emails.update(emails_on_home)

    doc = Document(initial_html)
    cleaned_html = doc.summary()
    soup = BeautifulSoup(cleaned_html, 'html.parser')
    home_page_text = soup.get_text(separator='\n', strip=True)

    if home_page_text:
        found_pages["home"] = {
            "url": start_url,
            "text": home_page_text
        }

    # --- Part 2: Find links and scrape other pages ---
    candidate_links = set()
    full_soup = BeautifulSoup(initial_html, 'html.parser')
    for link in full_soup.find_all("a", href=True):
        href = urljoin(start_url, link['href'])
        if is_valid_internal_link(start_url, href) and href != start_url:
            candidate_links.add(href)

    for url in candidate_links:
        if len(found_pages) >= max_pages:
            print("Reached max pages limit.")
            break

        for keyword in keywords:
            if keyword in url.lower() and keyword not in found_pages:
                # We need the full text to find emails
                try:
                    page_resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    page_resp.raise_for_status()
                    page_html = page_resp.text

                    emails_on_page = re.findall(email_regex, page_html)
                    all_emails.update(emails_on_page)

                    content = get_readable_text(url)
                    if content:
                        found_pages[keyword] = {
                            "url": url,
                            "text": content
                        }
                except requests.RequestException:
                    # If a sub-page fails, just skip it
                    print(f"  -> Could not scrape sub-page: {url}")
                break 

    # --- Part 3: Return the pages and the first email found ---
    first_email = list(all_emails)[0] if all_emails else None
    if first_email:
        print(f"[SUCCESS] Found contact email: {first_email}")

    return {"pages": found_pages, "email": first_email}