import re
from urllib.parse import urljoin, urlparse

import requests
import tldextract
from bs4 import BeautifulSoup
from readability import Document

from playwright.sync_api import sync_playwright
import re



def is_valid_internal_link(base_url, link):
    if not link:
        return False
    if link.startswith("#") or link.startswith("mailto:") or link.startswith("tel:"):
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
        if not resp.text.strip():  # skip empty pages
            print("  -> Page is empty, skipping.")
            return None
    except requests.RequestException:
        return None

    try:
        doc = Document(resp.text)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        print(f"  -> Could not parse page with readability: {e}")
        return None

def is_blank_or_low_content(text: str) -> bool:
    """
    Heuristically determine if a page has too little or meaningless content.
    Returns True if the page should be skipped.
    """
    if not text or not text.strip():
        return True #Blank/Whitespace Check

    #normalize text
    lowered = text.lower()

    # Common filler or placeholder phrases
    filler_phrases = [
        "coming soon",
        "under construction",
        "welcome to our website",
        "site under maintenance",
        "home page",
        "thank you for visiting",
        "this page is currently being updated",
        "temporarily unavailable",
        "page not found",
    ]

    if any(phrase in lowered for phrase in filler_phrases):
        return True #Phrase Check

    # Count words
    words = re.findall(r"\b\w+\b", text)
    if len(words) < 35:
        return True

    #Unique Word Ratio Check
    unique_ratio = len(set(words)) / len(words) if words else 0
    if unique_ratio < 0.25:
        return True

    return False


# def crawl_website(start_url, keywords=None, max_pages=10):
#     """
#     Crawls a website using Playwright, extracts text from relevant pages,
#     and finds the first email address.
#     """
    
#     if keywords is None:
#         keywords = [
#             "about", "team", "services", "careers", "contact",
#             "servicii", "despre", "despre-noi", "despre-mine",
#             "echipa", "cariera", "contacte", "oferte", "produse", "preturi",
#         ]

#     found_pages = {}
#     all_emails = set()
    
#     print(f"Scraping website: {start_url}")
    
#     with sync_playwright() as p:
#         browser = p.firefox.launch(headless=False)
#         page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
#         # Get home page
#         try:
#             page.goto(start_url, timeout=15000)
#             page.wait_for_load_state("domcontentloaded", timeout=10000)
            
#             # Cookie handling
#             dismiss_cookies(page)
#             page.wait_for_timeout(500)
#             remove_overlays(page)
            
#             # Extra wait for page to settle
#             page.wait_for_timeout(1000)
            
#             initial_html = page.content()
#         except Exception as e:
#             print(f"Fatal: Could not fetch start_url. Error: {e}")
#             browser.close()
#             return {"pages": {}, "email": None}

#         # Extract emails
#         email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
#         emails_on_home = re.findall(email_regex, initial_html)
#         all_emails.update(emails_on_home)
        
#         # Process home page
#         try:
#             # First, try with Readability
#             doc = Document(initial_html)
#             cleaned_html = doc.summary()
#             soup = BeautifulSoup(cleaned_html, "html.parser")
#             home_page_text = soup.get_text(separator="\n", strip=True)
            
#             # If Readability gives us very little content, try direct extraction
#             if len(home_page_text) < 500:
#                 print("  -> Readability extracted too little, trying direct extraction...")
#                 soup_full = BeautifulSoup(initial_html, "html.parser")
                
#                 # Remove cookie/script/style elements from full HTML
#                 for element in soup_full(['script', 'style', 'noscript', 'iframe']):
#                     element.decompose()
                
#                 # Remove known cookie banner elements
#                 for selector in ['[id*="cookie"]', '[class*="cookie"]', '[id*="consent"]', 
#                                 '[class*="consent"]', '[id*="gdpr"]', '[class*="gdpr"]']:
#                     for el in soup_full.select(selector):
#                         el.decompose()
                
#                 # Try to find main content areas
#                 main_content = (soup_full.find('main') or 
#                               soup_full.find('article') or 
#                               soup_full.find('div', {'id': 'content'}) or
#                               soup_full.find('div', {'class': 'content'}) or
#                               soup_full.find('body'))
                
#                 if main_content:
#                     home_page_text = main_content.get_text(separator="\n", strip=True)
            
#             # DEBUG: Print what we actually extracted
#             print("\n" + "="*80)
#             print("HOME PAGE EXTRACTED TEXT (first 1000 chars):")
#             print("="*80)
#             print(home_page_text[:1000])
#             print("="*80)
#             print(f"Total length: {len(home_page_text)} characters\n")
            
#             from_module = globals().get('is_blank_or_low_content')
#             if not from_module or not from_module(home_page_text):
#                 found_pages["home"] = {"url": start_url, "text": home_page_text}
#             else:
#                 print("  -> Home page content too low, skipping")
#         except Exception as e:
#             print(f"Could not parse homepage: {e}")
                
#         # Find candidate links
#         full_soup = BeautifulSoup(initial_html, "html.parser")
#         candidate_links = set()
#         for link in full_soup.find_all("a", href=True):
#             href = urljoin(start_url, link["href"])
#             from_module = globals().get('is_valid_internal_link')
#             if from_module and from_module(start_url, href) and href != start_url:
#                 candidate_links.add(href)
                
#         # Visit subpages
#         for url in candidate_links:
#             if len(found_pages) >= max_pages:
#                 print("Reached max pages limit")
#                 break

#             for keyword in keywords:
#                 if keyword in url.lower() and keyword not in found_pages:
#                     try:
#                         page.goto(url, timeout=15000)
#                         page.wait_for_load_state("domcontentloaded", timeout=10000)
#                         page.wait_for_timeout(500)
                        
#                         # Remove cookie banners from subpages too!
#                         remove_overlays(page)
#                         page.wait_for_timeout(500)
                        
#                         page_html = page.content()
#                         emails_on_page = re.findall(email_regex, page_html)
#                         all_emails.update(emails_on_page)

#                         # Try Readability first
#                         doc = Document(page_html)
#                         cleaned_page = doc.summary()
#                         soup = BeautifulSoup(cleaned_page, "html.parser")
#                         content = soup.get_text(separator="\n", strip=True)
                        
#                         # If Readability gives us very little, try direct extraction
#                         if len(content) < 500:
#                             print(f"    -> Readability gave {len(content)} chars, trying direct extraction...")
#                             soup_full = BeautifulSoup(page_html, "html.parser")
                            
#                             # Remove junk elements
#                             for element in soup_full(['script', 'style', 'noscript', 'iframe']):
#                                 element.decompose()
                            
#                             # Remove cookie banners
#                             for selector in ['[id*="cookie"]', '[class*="cookie"]', '[id*="consent"]', 
#                                            '[class*="consent"]', '[id*="gdpr"]', '[class*="gdpr"]']:
#                                 for el in soup_full.select(selector):
#                                     el.decompose()
                            
#                             # Find main content
#                             main_content = (soup_full.find('main') or 
#                                           soup_full.find('article') or 
#                                           soup_full.find('div', {'id': 'content'}) or
#                                           soup_full.find('div', {'class': 'content'}) or
#                                           soup_full.find('body'))
                            
#                             if main_content:
#                                 content = main_content.get_text(separator="\n", strip=True)
                        
#                         # DEBUG: Print subpage content
#                         print(f"\n{'='*80}")
#                         print(f"SUBPAGE '{keyword}' EXTRACTED TEXT (first 500 chars):")
#                         print(f"{'='*80}")
#                         print(content[:500])
#                         print(f"{'='*80}")
#                         print(f"Total length: {len(content)} characters\n")
                        
#                         if content:
#                             found_pages[keyword] = {"url": url, "text": content}
#                             print(f"  -> ✓ Scraped: {url}")
#                         else:
#                             print(f"  -> Content too low: {url}")
#                     except Exception as e:
#                         print(f"  -> Could not scrape: {url} - {e}")
#                     break
                    
#         browser.close()
        
#     # Return results
#     first_email = list(all_emails)[0] if all_emails else None
#     if first_email:
#         print(f"[SUCCESS] Found contact email: {first_email}")
        
#     return {"pages": found_pages, "email": first_email}

def crawl_website(start_url, keywords=None, max_pages=10):
    """
    Crawls a website using Playwright, extracts text from relevant pages,
    and finds the first email address, prioritizing the contact page email,
    using partial matching on URL path stems.
    """
    
    # 1. SIMPLIFIED STEMS FOR CONTEXTUAL PAGES (Partial Matching)
    CONTEXT_STEMS = [
        "about", "team", "mission", "vision", "leader", "story", "what-we-do",
        "service", "despre", "echipa", "cariera", "oferte", "produse", "pretur"
    ]
    
    # 2. SIMPLIFIED STEMS FOR CONTACT PAGES (for email prioritization)
    CONTACT_STEMS = ["contact", "get-in-touch", "getintouch"]
    
    # Combine all unique stems for the scraping loop
    ALL_STEMS = list(set(CONTEXT_STEMS + CONTACT_STEMS))

    found_pages = {}
    all_emails = set() # For deduplication and backup tracking
    
    # NEW: Variables for explicit email selection
    first_email_found = None # The very first email found (the backup)
    best_email = None        # The prioritized email (from contact page)

    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    
    print(f"Scraping website: {start_url}")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # --- Home Page Fetch and Processing ---
        try:
            page.goto(start_url, timeout=15000)
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            
            dismiss_cookies(page)
            page.wait_for_timeout(500)
            remove_overlays(page)
            page.wait_for_timeout(1000)
            
            initial_html = page.content()
        except Exception as e:
            print(f"Fatal: Could not fetch start_url. Error: {e}")
            browser.close()
            return {"pages": {}, "email": None}

        # Extract emails on home
        emails_on_home = re.findall(email_regex, initial_html)
        all_emails.update(emails_on_home)
        
        # 1. Capture the very first email found on the home page as the default backup
        if emails_on_home and first_email_found is None:
            first_email_found = emails_on_home[0]
            print(f"  -> Backup email found on home page: {first_email_found}")
        
        # Process home page (Content extraction logic remains the same)
        try:
            doc = Document(initial_html)
            soup = BeautifulSoup(doc.summary(), "html.parser")
            home_page_text = soup.get_text(separator="\n", strip=True)
            
            # Simplified direct extraction fallback for brevity
            if len(home_page_text) < 500:
                soup_full = BeautifulSoup(initial_html, "html.parser")
                main_content = soup_full.find('main') or soup_full.find('body')
                if main_content:
                    home_page_text = main_content.get_text(separator="\n", strip=True)
            
            from_module = globals().get('is_blank_or_low_content')
            if not from_module or not from_module(home_page_text):
                found_pages["home"] = {"url": start_url, "text": home_page_text}
            else:
                print("  -> Home page content too low, skipping")
        except Exception as e:
            print(f"Could not parse homepage: {e}")

        # Find candidate links and prepare URL list
        full_soup = BeautifulSoup(initial_html, "html.parser")
        candidate_links = set()
        for link in full_soup.find_all("a", href=True):
            href = urljoin(start_url, link["href"])
            if is_valid_internal_link(start_url, href) and href != start_url:
                candidate_links.add(href)
                
        # --- Subpage Scraping with Partial Matching ---
        url_list = list(candidate_links)
        
        for url in url_list:
            if len(found_pages) >= max_pages:
                print("Reached max pages limit")
                break
            
            # Skip if we already found the priority email
            if best_email is not None:
                 # We still want to scrape context pages, so we only break if the current page is not a context page
                 # However, we should prioritize scraping context pages (e.g., 'about') even after finding an email.
                 # We only check if the current page stem is already scraped.
                pass 

            matched_stem = None
            url_lower = url.lower()
            
            # Use regex to find a match for any stem in the URL path.
            for stem in ALL_STEMS:
                if re.search(f'/{stem}[^/]*', url_lower):
                    if stem not in found_pages:
                        matched_stem = stem
                        break
            
            if matched_stem:
                try:
                    print(f"  -> Scraping page for stem: '{matched_stem}' at {url}")
                    page.goto(url, timeout=15000)
                    page.wait_for_load_state("domcontentloaded", timeout=10000)
                    page.wait_for_timeout(500)
                    
                    remove_overlays(page)
                    page.wait_for_timeout(500)
                    
                    page_html = page.content()
                    emails_on_page = re.findall(email_regex, page_html)
                    all_emails.update(emails_on_page)

                    # 2. EMAIL SELECTION LOGIC: Prioritize contact page email
                    # Check if this page matches a contact stem AND we haven't found a best email yet
                    if matched_stem in CONTACT_STEMS and emails_on_page and best_email is None:
                        # Only take the first one found on this dedicated page
                        best_email = list(emails_on_page)[0]
                        print(f"  -> Found prioritized contact-specific email: {best_email}")

                    # Content scraping (existing logic)
                    doc = Document(page_html)
                    soup = BeautifulSoup(doc.summary(), "html.parser")
                    content = soup.get_text(separator="\n", strip=True)
                    
                    # Store content using the stem as the key
                    if content and not is_blank_or_low_content(content):
                        found_pages[matched_stem] = {"url": url, "text": content}
                        print(f"  -> ✓ Scraped content for stem: {matched_stem}")
                    else:
                        print(f"  -> Content too low: {url}")
                except Exception as e:
                    print(f"  -> Could not scrape: {url} - {e}")
                    
        browser.close()
        
    # --- 3. Final Email Selection ---
    # Use best_email (from contact page) if found, otherwise use first_email_found (backup)
    final_email = best_email if best_email else first_email_found
    
    if final_email:
        print(f"[SUCCESS] Found contact email: {final_email}")
        
    return {"pages": found_pages, "email": final_email}

def dismiss_cookies(page):
    """
    Attempts to automatically accept cookie banners with conservative targeting.
    Focus: ONLY click primary accept buttons, avoid settings/details links.
    """
    
    # CONSERVATIVE text matching - only clear "accept" language
    ACCEPT_KEYWORDS = [
        # English - be specific
        "accept all", "accept cookies", "agree and close", "i accept", 
        "allow all", "accept and continue", "i agree",
        
        # Romanian - specific accept phrases (with and without diacritics)
        "acceptă tot", "accepta tot", "accept tot",
        "acceptă toate", "accepta toate", "accept toate",
        "sunt de acord", "de acord",
        "acceptă cookie", "accepta cookie", "accept cookie",
        "acceptă și închide", "accepta si inchide", "accept si inchide",
        "în regulă", "in regula",
        "permite tot", "permite toate",
        "continua", "continuă",
    ]
    
    # Known good selectors for major cookie platforms
    KNOWN_ACCEPT_SELECTORS = [
        # CookieScript (very common in Romania)
        '#cookiescript_accept',
        'button[data-cs-accept-all]',
        '.cookiescript-accept',
        
        # OneTrust
        '#onetrust-accept-btn-handler',
        '#accept-recommended-btn-handler',
        
        # Cookiebot (popular in EU)
        '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
        '#CybotCookiebotDialogBodyButtonAccept',
        '.CybotCookiebotDialogBodyButton',
        
        # Common Romanian patterns
        'button[id*="accepta"]',
        'button[class*="accepta"]',
        'button[id*="accept-all"]',
        'button[class*="accept-all"]',
        'button[id*="cookie-accept"]',
        'button[class*="cookie-accept"]',
        '.cookie-consent-accept',
        '.btn-accept-cookies',
        '#accept-cookies',
        '#acceptCookies',
        
        # GDPR generic
        'button[aria-label*="Accept"]',
        'button[aria-label*="Acceptă"]',
        'button[aria-label*="Accepta"]',
    ]
    
    print("  -> Attempting to dismiss cookie banner...")
    
    # --- STRATEGY 1: Known Selectors (Most Reliable) ---
    for selector in KNOWN_ACCEPT_SELECTORS:
        try:
            if page.locator(selector).first.is_visible(timeout=2000):
                page.locator(selector).first.click(timeout=3000)
                print(f"  -> ✓ Clicked via known selector: {selector}")
                page.wait_for_timeout(1000)  # Wait for banner to close
                return True
        except Exception:
            continue
    
    # --- STRATEGY 2: iFrame Handling (CookieScript often uses iframes) ---
    try:
        iframe = page.frame_locator('iframe[id*="cookiescript"]')
        accept_btn = iframe.locator('#cookiescript_accept')
        if accept_btn.is_visible(timeout=3000):
            accept_btn.click()
            print("  -> ✓ Clicked CookieScript accept in iframe")
            page.wait_for_timeout(1000)
            return True
    except Exception:
        pass
    
    # --- STRATEGY 3: Conservative Text Matching ---
    for keyword in ACCEPT_KEYWORDS:
        try:
            # Look for buttons with exact text match (case insensitive)
            selector = f'button:has-text("{keyword}")'
            buttons = page.locator(selector)
            
            # Get count of matches
            count = buttons.count()
            if count > 0:
                # Click the first visible one
                for i in range(count):
                    try:
                        btn = buttons.nth(i)
                        if btn.is_visible(timeout=1000):
                            btn.click(timeout=2000)
                            print(f"  -> ✓ Clicked via text: '{keyword}'")
                            page.wait_for_timeout(1000)
                            return True
                    except Exception:
                        continue
        except Exception:
            continue
    
    # --- STRATEGY 4: Nuclear Option (Only if nothing else worked) ---
    print("  -> No accept button found, trying overlay removal...")
    try:
        page.evaluate("""
            // Only target common cookie banner containers
            const selectors = [
                '[id*="cookie"]',
                '[class*="cookie"]',
                '[id*="consent"]',
                '[class*="consent"]',
                '[id*="gdpr"]',
                '[class*="gdpr"]'
            ];
            
            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    // Only hide if it's position fixed/sticky (likely a banner)
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.style.setProperty('display', 'none', 'important');
                    }
                });
            });
            
            // Re-enable scrolling
            document.body.style.setProperty('overflow', 'auto', 'important');
            document.documentElement.style.setProperty('overflow', 'auto', 'important');
        """)
        print("  -> ✓ Forced overlay removal")
        return True
    except Exception as e:
        print(f"  -> ✗ Could not remove overlays: {e}")
    
    print("  -> No cookie banner found or already dismissed")
    return False

        

def remove_overlays(page):
    """
    Remove any remaining fixed overlays AND cookie banner DOM elements.
    Call this AFTER cookie dismissal.
    """
    try:
        page.evaluate("""
            // Remove common blocking overlays
            document.querySelectorAll('[class*="modal-backdrop"], [class*="overlay"]').forEach(el => {
                if (window.getComputedStyle(el).position === 'fixed') {
                    el.remove();
                }
            });
            
            // CRITICAL: Remove cookie banner DOM elements entirely
            const cookieSelectors = [
                '[id*="cookie"]',
                '[class*="cookie"]',
                '[id*="consent"]', 
                '[class*="consent"]',
                '[id*="gdpr"]',
                '[class*="gdpr"]',
                '[id*="cookiescript"]',
                '[class*="cookiescript"]',
                '[id*="CybotCookiebot"]',
                '[class*="CybotCookiebot"]',
                '[id*="onetrust"]',
                '[class*="onetrust"]'
            ];
            
            cookieSelectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    // Remove elements that look like banners/modals
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || 
                        style.position === 'sticky' || 
                        style.position === 'absolute' ||
                        el.getAttribute('role') === 'dialog' ||
                        el.getAttribute('aria-modal') === 'true') {
                        console.log('Removing cookie element:', el);
                        el.remove();
                    }
                });
            });
        """)
        print("  -> ✓ Removed cookie banner DOM elements")
    except Exception as e:
        print(f"  -> Could not remove overlays: {e}")