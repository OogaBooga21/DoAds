from playwright.sync_api import sync_playwright
import csv
import time


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
            continue # Skip items in the second list that don't have the merge key.
            
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

def extract_info(page,business_cards,max_results):
    total = min(business_cards.count(), max_results)
    print(f"[INFO] Found {business_cards.count()} businesses. Getting top {total} names and links.")

    results = []

    for i in range(total):
        card = business_cards.nth(i)
        card.scroll_into_view_if_needed()
        name = card.get_attribute("aria-label")
            
        website_locator = page.locator('a[data-value="Website"]')
                
        website_href = "No Website" # Default value
                # Check if the locator found any elements
        if website_locator.count() > 0:
            href = card.first.get_attribute('href')
            if href:
                website_href = href
                print(f"  [SUCCESS] Found website: {website_href}")
        else:
            print("  [INFO] No website link found for this business.")
                

        results.append({
            "name": name,
            "link": website_href
        })
    return results

def get_leads_from_Maps(query,output_csv="leads.csv", max_results=50, search_for=1): #0 both, 1 only with websites, 2 only without websites
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Set to True to hide browser
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        print("[INFO] Navigating to Google Maps...")
        page.goto("https://www.google.com/maps?hl=en", timeout=60000) # 1 min

        # Optional: Accept consent if shown
        try:
            page.click('button:has-text("Accept")', timeout=10000) # 10 sec
            print("[INFO] Accepted cookies.")
        except:
            print("[INFO] No cookie popup found.")

        # Wait for search box and input query
        search_box = page.locator('input#searchboxinput')
        search_box.wait_for(timeout=10000) #10 sec
        search_box.fill(query)
        search_box.press("Enter")

        # Wait for the results list to load
        print("[INFO] Waiting for results...")
        try:
            page.wait_for_selector('div[role="feed"]', timeout=120000) #2 min
            print("[INFO] Results loaded.")
        except:
            print("[ERROR] No results found.")
            browser.close()
            return []

        # Scroll the results panel to load more businesses
        scrollable_div = page.locator('div[role="feed"]')
        for i in range(8): ##############################################################################################
            scrollable_div.evaluate("el => el.scrollBy(0, el.scrollHeight)")
            print(f"[INFO] Scrolling... ({i+1}/8)")
            time.sleep(2)

        results1 = []
        results2 = []
        # Collect business cards
        if search_for == 0 or search_for == 1:
            business_cards = page.locator('a[data-value="Website"]') # with website
            results1=extract_info(page, business_cards, max_results)
        if search_for == 0 or search_for == 2:
            business_cards = page.locator('a[href*="/place/"]') # without website
            results2=extract_info(page, business_cards, max_results)
        
        results = combine_results(results1, results2, merge_key="name")

        return results