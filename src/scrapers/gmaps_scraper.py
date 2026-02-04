import re
import csv
import time

from playwright.sync_api import sync_playwright


def combine_results(list1, list2, merge_key="name"):
    """
    Merges two lists of dictionaries based on a common key.

    Args:
        list1 (list): The first list of dictionaries.
        list2 (list): The second list of dictionaries.
        merge_key (str): The common key to match dictionaries on (e.g., 'name').

    Returns:
        list: A new list containing the merged dictionaries.
    """
    # Create a lookup map from the first list for efficient merging.
    # The key of the map is the value of the merge_key (e.g., the name 'Company A'),
    # and the value is the entire dictionary.
    merged_data = {item[merge_key]: item for item in list1 if merge_key in item}

    # Iterate through the second list to merge with the first.
    for item in list2:
        if merge_key not in item:
            continue  # Skip items in the second list that don't have the merge key.

        key = item[merge_key]
        if key in merged_data:
            # If the key already exists, update the dictionary in our map.
            # .update() adds new key-value pairs and overwrites existing ones.
            merged_data[key].update(item)
        else:
            # If the key is new, add the whole item to our map.
            merged_data[key] = item

    # Return the final merged dictionaries as a list.
    return list(merged_data.values())


def extract_info(card_locator):
    website_href = "No Website"
    # Try to find a link with an aria-label containing "website"
    website_locator = card_locator.locator('a[aria-label*="website" i]').nth(0)
    if website_locator.count() > 0:
        website_href = website_locator.get_attribute('href')
    else:
        # Fallback: Try to find a link that contains the text "Website" or "Site web"
        website_locator = card_locator.locator('a:has-text("Website"), a:has-text("Site web")').nth(0)
        if website_locator.count() > 0:
            website_href = website_locator.get_attribute('href')

    phone_locator = card_locator.locator('button[data-tooltip="Copy phone number"]').nth(0)

    name = card_locator.get_attribute('aria-label') if card_locator.count() > 0 else "No Name"
    phone = phone_locator.get_attribute('aria-label') if phone_locator.count() > 0 else "No Phone"
    
    if phone and "Copy phone number" in phone:
        phone = phone.replace("Copy phone number", "").strip()

    return {"name": name, "link": website_href, "phone": phone}


def get_leads_from_Maps(
    query, output_csv="leads.csv", max_results=50, search_for=1
):  # 0 both, 1 only with websites, 2 only without websites
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])  # Set to True to hide browser
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        print("[INFO] Navigating to Google Maps...")
        page.goto("https://www.google.com/maps?hl=en", timeout=120000)  # 2 min

        # More robustly accept consent
        consent_accepted = False
        for button_text in ["Accept all", "Accept", "I agree"]:
            try:
                page.get_by_role("button", name=button_text, exact=True).click(timeout=5000)
                print(f"[INFO] Accepted cookies with text: '{button_text}'")
                consent_accepted = True
                break
            except Exception:
                continue
        
        if not consent_accepted:
            print("[INFO] No standard cookie popup found or handled.")



        # Wait for search box and input query
        search_box = page.locator('input[name="q"][role="combobox"]')
        search_box.wait_for(timeout=30000)  # 30 sec
        search_box.fill(query)
        search_box.press("Enter")

        # Wait for the results list to load
        print("[INFO] Waiting for results...")
        try:
            page.wait_for_selector('div[role="feed"]', timeout=120000)  # 2 min
            print("[INFO] Results loaded.")
        except:
            print("[ERROR] No results found.")
            browser.close()
            return []

        # Scroll the results panel to load more businesses
        scrollable_div = page.locator('div[role="feed"]')
        for i in range(
            10
        ):  ##############################################################################################
            scrollable_div.evaluate("el => el.scrollBy(0, el.scrollHeight)")
            print(f"[INFO] Scrolling... ({i+1}/8)")
            time.sleep(2)

        results = []
        business_cards = page.locator('div[role="article"][class*="Nv2PK"]').all()
        
        total = min(len(business_cards), max_results)
        print(f"[INFO] Found {len(business_cards)} businesses. Getting top {total}.")

        for i in range(total):
            card = business_cards[i]
            
            info = extract_info(card)
            
            if search_for == 1 and info['link'] == "No Website":
                continue
            if search_for == 2 and info['link'] != "No Website":
                continue
                
            results.append(info)

        return results
