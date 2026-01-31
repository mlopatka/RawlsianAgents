"""
Step 3 (optional): Import pre-crawled talk data from JSON into Couchbase.
Expects talk_results1.json with list of objects containing at least 'url'.
"""
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Couchbase imports – install with: pip install couchbase
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import DocumentExistsException


def get_collection():
    """Connect to Couchbase and return the target collection."""
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
    return cluster, collection


def save_to_couchbase():
    try:
        with open("talk_results1.json", "r") as f:
            talks = json.load(f)

        cluster, collection = get_collection()
        successful = failed = 0

        for talk in talks:
            try:
                talk["crawled_at"] = datetime.utcnow().isoformat()
                doc_key = f"talk_{talk['url'].split('/')[-1]}"
                try:
                    collection.insert(doc_key, talk)
                    print(f"Stored: {talk.get('url', doc_key)}")
                    successful += 1
                except DocumentExistsException:
                    collection.upsert(doc_key, talk)
                    print(f"Updated: {talk.get('url', doc_key)}")
                    successful += 1
            except Exception as e:
                print(f"Error storing {talk.get('url', '?')}: {e}")
                failed += 1

        print(f"\nDone: {successful} stored/updated, {failed} failed.")
        cluster.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    save_to_couchbase()
