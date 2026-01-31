"""
Step 2: Crawl talk pages from event_urls.txt and store structured data in Couchbase.
Uses crawl4ai AsyncWebCrawler; customize extract_talk_info() for your HTML layout.
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

try:
    from crawl4ai import AsyncWebCrawler
except ImportError:
    AsyncWebCrawler = None

from bs4 import BeautifulSoup
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import DocumentExistsException

load_dotenv()

BATCH_SIZE = 5


async def extract_talk_info(html_content: str) -> dict:
    """
    Parse HTML and return structured talk info.
    Customize selectors for your conference schedule page structure.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    talk_info = {
        "title": "Unknown",
        "description": "No description available",
        "speaker": "Unknown",
        "category": "Uncategorized",
        "date": "Unknown",
        "location": "Unknown",
    }

    # Example selectors – adjust to your HTML
    title_elem = soup.find("span", class_="event")
    if title_elem:
        name_elem = title_elem.find("a", class_="name")
        if name_elem:
            talk_info["title"] = name_elem.text.strip()

    desc_elem = soup.find("div", class_="tip-description")
    if desc_elem:
        talk_info["description"] = desc_elem.text.strip()

    speakers_div = soup.find("div", class_="sched-event-details-roles")
    if speakers_div:
        speaker_elems = speakers_div.find_all("h2")
        speakers = []
        for se in speaker_elems:
            a = se.find("a")
            if a:
                speakers.append(a.text.strip())
        if speakers:
            talk_info["speaker"] = " & ".join(speakers)

    category_elem = soup.find("div", class_="sched-event-type")
    if category_elem:
        a = category_elem.find("a")
        if a:
            talk_info["category"] = a.text.strip()

    time_place = soup.find("div", class_="sched-event-details-timeandplace")
    if time_place:
        parts = time_place.get_text().split("\n")
        if parts:
            talk_info["date"] = parts[0].strip()
        loc_link = time_place.find("a")
        if loc_link:
            talk_info["location"] = loc_link.text.strip()

    return talk_info


async def crawl_talks():
    if not AsyncWebCrawler:
        print("Error: crawl4ai not installed. pip install crawl4ai")
        return

    try:
        with open("event_urls.txt", "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: event_urls.txt not found. Run extract_events.py first.")
        return

    if not urls:
        print("No URLs in event_urls.txt")
        return

    connection_string = os.getenv("CB_CONNECTION_STRING")
    username = os.getenv("CB_USERNAME")
    password = os.getenv("CB_PASSWORD")
    bucket_name = os.getenv("CB_BUCKET")
    collection_name = os.getenv("CB_COLLECTION")

    if not all([connection_string, username, password, bucket_name, collection_name]):
        raise ValueError("Missing required Couchbase environment variables")

    auth = PasswordAuthenticator(username, password)
    options = ClusterOptions(auth)
    cluster = Cluster(connection_string, options)
    cluster.ping()

    bucket = cluster.bucket(bucket_name)
    collection = bucket.collection(collection_name)

    successful_crawls = failed_crawls = 0

    async with AsyncWebCrawler() as crawler:
        for i in range(0, len(urls), BATCH_SIZE):
            batch_urls = urls[i : i + BATCH_SIZE]
            try:
                batch_results = await crawler.arun_many(batch_urls)
                for url, result in zip(batch_urls, batch_results):
                    try:
                        if result and result.html:
                            talk_info = await extract_talk_info(result.html)
                            talk_info["url"] = url
                            talk_info["crawled_at"] = datetime.utcnow().isoformat()
                            doc_key = f"talk_{url.split('/')[-1]}"
                            try:
                                collection.insert(doc_key, talk_info)
                                print(f"Stored: {url}")
                                successful_crawls += 1
                            except DocumentExistsException:
                                collection.upsert(doc_key, talk_info)
                                print(f"Updated: {url}")
                                successful_crawls += 1
                        else:
                            print(f"Failed to crawl: {url}")
                            failed_crawls += 1
                    except Exception as e:
                        print(f"Error {url}: {e}")
                        failed_crawls += 1
            except Exception as e:
                print(f"Batch error: {e}")
            await asyncio.sleep(1)

    print(f"\nDone: {successful_crawls} stored/updated, {failed_crawls} failed.")
    cluster.close()


if __name__ == "__main__":
    asyncio.run(crawl_talks())
