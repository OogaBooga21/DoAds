import re
import requests

# Common free/public email domains to ignore
FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com", "icloud.com"}


def extract_domains(emails):
    domains = set()
    for email in emails:
        match = re.match(r"[^@]+@([^@]+)", email)
        if match:
            domain = match.group(1).lower()
            if domain not in FREE_DOMAINS:
                domains.add(domain)
    return domains


def get_websites(domains):
    websites = {}
    for domain in domains:
        url = f"https://{domain}"
        try:
            r = requests.head(url, timeout=5, allow_redirects=True)
            if r.status_code < 400:
                websites[domain] = url
            else:
                websites[domain] = None
        except requests.RequestException:
            websites[domain] = None
    return websites


if __name__ == "__main__":
    sample_emails = [
        "alice@gmail.com",
        "bob@acmeinc.com",
        "carol@startup.io",
        "dave@yahoo.com"
    ]

    domains = extract_domains(sample_emails)
    websites = get_websites(domains)

    print("Extracted Websites:")
    for domain, site in websites.items():
        print(domain, "->", site)
