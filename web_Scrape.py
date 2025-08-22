# # import requests
# # from bs4 import BeautifulSoup
# # from readability import Document

# # def scrape_website(url):
# #     headers = {
# #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# #     }

# #     try:
# #         response = requests.get(url, headers=headers, timeout=10)
# #         response.raise_for_status()
# #     except requests.RequestException as e:
# #         return f"Error fetching the website: {e}"

# #     # Use readability-lxml to get clean content
# #     doc = Document(response.text)
# #     title = doc.title()
# #     cleaned_html = doc.summary()

# #     # Parse the cleaned HTML to get the readable text
# #     soup = BeautifulSoup(cleaned_html, 'html.parser')
# #     main_text = soup.get_text(separator='\n', strip=True)

# #     return {
# #         "title": title,
# #         "text": main_text,
# #         "url": url
# #     }

# # # Example usage
# # if __name__ == "__main__":
# #     url = "https://www.dial911fordesign.com/"
# #     info = scrape_website(url)
# #     print(f"Title: {info['title']}\n")
# #     print(f"Text:\n{info['text']}")

# import requests
# from bs4 import BeautifulSoup
# from readability import Document
# from urllib.parse import urljoin, urlparse
# import tldextract

# def is_valid_internal_link(base_url, link):
#     if not link:
#         return False
#     parsed_link = urlparse(urljoin(base_url, link))
#     base_domain = tldextract.extract(base_url).domain
#     link_domain = tldextract.extract(parsed_link.netloc).domain
#     return base_domain == link_domain

# def get_readable_text(url):
#     try:
#         resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
#         resp.raise_for_status()
#     except requests.RequestException:
#         return None

#     doc = Document(resp.text)
#     soup = BeautifulSoup(doc.summary(), 'html.parser')
#     return soup.get_text(separator='\n', strip=True)

# def crawl_website(start_url, keywords=None, max_pages=10):
#     if keywords is None:
#         keywords = ["about", "team", "services", "careers", "contact"]
    
#     found_pages = {}
    
#     # --- Part 1: Always scrape the Home Page first ---
#     # It's our source for content and for finding other important links.
#     print(f"Scraping home page: {start_url}")
#     try:
#         resp = requests.get(start_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
#         resp.raise_for_status()
#     except requests.RequestException as e:
#         print(f"Fatal: Could not fetch the start_url. Exiting. Error: {e}")
#         return {}

#     soup = BeautifulSoup(resp.text, 'html.parser')
    
#     # Save home page content
#     for script in soup(["script", "style"]):
#         script.extract()
#     home_text = " ".join(soup.get_text().split())
#     if home_text:
#         found_pages["home"] = {
#             "url": start_url,
#             "text": home_text
#         }

#     # --- Part 2: Find all links on the home page and scrape ONLY if they match keywords ---
#     candidate_links = set()
#     for link in soup.find_all("a", href=True):
#         href = urljoin(start_url, link['href'])
#         if is_valid_internal_link(start_url, href):
#             candidate_links.add(href)

#     # Now, iterate through the links we found and only scrape the relevant ones
#     for url in candidate_links:
#         if len(found_pages) >= max_pages:
#             print("Reached max pages limit.")
#             break
        
#         for keyword in keywords:
#             if keyword in url.lower():
#                 # Avoid scraping if we already found a page for this keyword
#                 if keyword not in found_pages:
#                     content = get_readable_text(url)
#                     if content:
#                         found_pages[keyword] = {
#                             "url": url,
#                             "text": content
#                         }
#                 # Once a URL matches a keyword, we don't need to check it for other keywords
#                 break 

#     return found_pages


# # Example usage:
# if __name__ == "__main__":
#     url = "https://www.dial911fordesign.com/"
#     data = crawl_website(url)
#     for section, content in data.items():
#         print(f"\n--- {section.upper()} PAGE ---")
#         print(f"URL: {content['url']}")
#         print(f"Content Preview:\n{content['text'][:500]}...")


import requests
from bs4 import BeautifulSoup
from readability import Document
from urllib.parse import urljoin, urlparse
import tldextract

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

def crawl_website(start_url, keywords=None, max_pages=10):
    if keywords is None:
        keywords = ["about", "team", "services", "careers", "contact"]
    
    found_pages = {}
    
    # --- Part 1: Scrape and SUMMARIZE the Home Page using Transformers ---
    print(f"Scraping and summarizing home page: {start_url}")
    try:
        resp = requests.get(start_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Fatal: Could not fetch the start_url. Exiting. Error: {e}")
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # --- Clean and save the full readable text of the home page ---
    doc = Document(resp.text)
    cleaned_html = doc.summary()
    soup = BeautifulSoup(cleaned_html, 'html.parser')
    home_page_text = soup.get_text(separator='\n', strip=True)

    if home_page_text:
        found_pages["home"] = {
            "url": start_url,
            "text": home_page_text
        }
    
    # --- Part 2: Find links and get full content for other pages ---
    candidate_links = set()
    full_soup = BeautifulSoup(resp.text, 'html.parser')
    for link in full_soup.find_all("a", href=True):
        href = urljoin(start_url, link['href'])
        if is_valid_internal_link(start_url, href) and href != start_url:
            candidate_links.add(href)

    for url in candidate_links:
        if len(found_pages) >= max_pages:
            print("Reached max pages limit.")
            break
        
        for keyword in keywords:
            if keyword in url.lower():
                if keyword not in found_pages:
                    content = get_readable_text(url)
                    if content:
                        found_pages[keyword] = {
                            "url": url,
                            "text": content
                        }
                break 

    return found_pages


# # Example usage:
# if __name__ == "__main__":
#     url = "https://www.seedx.us/"
#     data = crawl_website(url, keywords=["capabilities", "about", "contact", "studies"])
    
#     print("\n\n--- CRAWL COMPLETE ---")
#     for section, content in data.items():
#         print(f"\n--- {section.upper()} PAGE ---")
#         print(f"URL: {content['url']}")
#         print(f"Content Preview:\n{content['text'][:1000]}...")