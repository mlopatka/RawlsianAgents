"""
Step 1: Extract event/talk URLs from HTML (e.g. conference schedule).
Reads HTML from stdin, merges with event_urls.txt, prints count of new URLs.
"""
import sys
from bs4 import BeautifulSoup

# Customize for your schedule page
BASE_URL = "https://example.com/schedule/"
URL_PREFIX = "event/"  # links containing this are considered event URLs


def extract_event_urls(html_content: str) -> set:
    """Extract event URLs from HTML. Override BASE_URL and URL_PREFIX as needed."""
    soup = BeautifulSoup(html_content, "html.parser")
    urls = set()
    for link in soup.find_all("a", href=True):
        href = link["href"].strip()
        if href.startswith(URL_PREFIX):
            full_url = href if href.startswith("http") else f"{BASE_URL.rstrip('/')}/{href.lstrip('/')}"
            urls.add(full_url)
    return urls


def main():
    html_input = sys.stdin.read()
    new_urls = extract_event_urls(html_input)

    existing_urls = set()
    try:
        with open("event_urls.txt", "r") as f:
            existing_urls = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        pass

    all_urls = sorted(existing_urls | new_urls)
    with open("event_urls.txt", "w") as f:
        for url in all_urls:
            f.write(url + "\n")

    added = len(new_urls - existing_urls)
    print(f"Added {added} new URLs. Total URLs in file: {len(all_urls)}")


if __name__ == "__main__":
    main()
