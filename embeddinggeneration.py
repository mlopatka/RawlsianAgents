"""
Step 4: Generate embeddings for Couchbase documents and store for vector search.
Requires an OpenAI-compatible embeddings endpoint (e.g. Nebius).
Use USE_LOCAL_LLM=1 to use a local embedding model (e.g. Ollama nomic-embed-text).
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from config import openai_base_url, openai_api_key, embedding_model

from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator


def get_couchbase_connection():
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
    return cluster, collection, bucket_name


def generate_embedding(text: str) -> list:
    """Call OpenAI-compatible embeddings API (cloud or local when USE_LOCAL_LLM=1)."""
    client = OpenAI(
        base_url=openai_base_url(),
        api_key=openai_api_key(),
    )
    response = client.embeddings.create(
        model=embedding_model(),
        input=text,
    )
    return response.data[0].embedding


def process_talks():
    try:
        cluster, collection, bucket_name = get_couchbase_connection()
        query = f'SELECT * FROM `{bucket_name}`'
        result = cluster.query(query)

        successful = failed = 0
        for row in result:
            try:
                doc = row[bucket_name]
                doc_key = f"talk_{doc['url'].split('/')[-1]}"
                combined_text = (
                    f"Title: {doc.get('title', '')}\n"
                    f"Description: {doc.get('description', '')}\n"
                    f"Category: {doc.get('category', '')}"
                )
                embedding = generate_embedding(combined_text)
                doc["embedding"] = embedding
                collection.upsert(doc_key, doc)
                print(f"Updated embedding: {doc.get('url', doc_key)}")
                successful += 1
            except Exception as e:
                print(f"Error processing document: {e}")
                failed += 1

        print(f"\nDone: {successful} processed, {failed} failed.")
        cluster.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    process_talks()
