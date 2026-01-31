"""
Step 5: Streamlit RAG app – research agent + vector search → final talk proposal.
Requires Couchbase with vector index and NEBIUS_API_* (or OpenAI-compatible) for embeddings/chat.
Use USE_LOCAL_LLM=1 or run with --local-llm to use a local open-source LLM (e.g. Ollama).
"""
import os
import sys
from datetime import timedelta
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Apply CLI flag so ADK and embedding code see USE_LOCAL_LLM
if "--local-llm" in sys.argv:
    os.environ["USE_LOCAL_LLM"] = "1"

from config import openai_base_url, openai_api_key, chat_model, embedding_model

from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, ClusterTimeoutOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.vector_search import VectorQuery, VectorSearch
from couchbase.search import SearchRequest, MatchNoneQuery

from adk_research_agent import run_adk_research

# OpenAI-compatible client (cloud or local when USE_LOCAL_LLM / --local-llm)
client = OpenAI(
    base_url=openai_base_url(),
    api_key=openai_api_key(),
)


class CouchbaseConnection:
    """Couchbase connection with vector search. Set CB_* and CB_SEARCH_INDEX in .env."""

    def __init__(self):
        connection_string = os.getenv("CB_CONNECTION_STRING")
        username = os.getenv("CB_USERNAME")
        password = os.getenv("CB_PASSWORD")
        bucket_name = os.getenv("CB_BUCKET")
        collection_name = os.getenv("CB_COLLECTION")

        if not all([connection_string, username, password, bucket_name, collection_name]):
            raise ValueError("Missing required Couchbase environment variables")

        auth = PasswordAuthenticator(username, password)
        timeout_options = ClusterTimeoutOptions(
            kv_timeout=timedelta(seconds=10),
            query_timeout=timedelta(seconds=20),
            search_timeout=timedelta(seconds=20),
        )
        options = ClusterOptions(auth, timeout_options=timeout_options)

        self.cluster = Cluster(connection_string, options)
        self.cluster.ping()

        self.bucket = self.cluster.bucket(bucket_name)
        self.scope = self.bucket.scope("_default")
        self.collection = self.bucket.collection(collection_name)
        self.search_index_name = os.getenv("CB_SEARCH_INDEX", "proposal_talks_index")

    def generate_embedding(self, text: str) -> List[float]:
        response = client.embeddings.create(
            model=embedding_model(),
            input=text,
            timeout=30,
        )
        return response.data[0].embedding

    def get_similar_talks(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        try:
            embedding = self.generate_embedding(query)
            search_req = SearchRequest.create(MatchNoneQuery()).with_vector_search(
                VectorSearch.from_vector_query(
                    VectorQuery("embedding", embedding, num_candidates=num_results)
                )
            )
            result = self.scope.search(
                self.search_index_name, search_req, timeout=timedelta(seconds=20)
            )
            rows = list(result.rows())

            similar_talks = []
            for row in rows:
                try:
                    doc = self.collection.get(row.id, timeout=timedelta(seconds=5))
                    if doc and doc.value:
                        talk = doc.value
                        similar_talks.append({
                            "title": talk.get("title", "N/A"),
                            "description": talk.get("description", "N/A"),
                            "category": talk.get("category", "N/A"),
                            "speaker": talk.get("speaker", "N/A"),
                            "score": row.score,
                        })
                except Exception as doc_error:
                    st.warning(f"Could not fetch document {row.id}: {doc_error}")
            return similar_talks
        except Exception as e:
            st.error(f"Vector search error: {e}")
            return []


def generate_talk_suggestion(
    query: str,
    similar_talks: List[Dict[str, Any]],
    adk_research: str,
) -> str:
    """Synthesize historical context + research into a final talk proposal."""
    historical_context = (
        "\n\n".join(
            f"Title: {t['title']}\nDescription: {t['description']}\nCategory: {t['category']}"
            for t in similar_talks
        )
        if similar_talks
        else "No similar historical talks found."
    )

    prompt = f"""You are an expert conference program advisor.
Create a compelling, unique talk proposal.

**User's idea:** "{query}"

**PART 1 – Historical context (similar past talks):**
{historical_context}

**PART 2 – Real-time research (current trends, gaps, sentiment):**
{adk_research}

**Task:** Synthesize the above into one complete proposal. Avoid repeating past talks; offer a fresh angle.

**Output format:**

**Title:**
*One compelling title.*

**Abstract:**
*2–3 paragraphs: landscape, new insights, and why this talk is timely.*

**Key learning objectives:**
*3–4 bullets.*

**Target audience:**
*Who this is for.*

**Why this talk is unique:**
*How it differs from past talks and aligns with current trends.*
"""

    try:
        response = client.chat.completions.create(
            model=chat_model(),
            messages=[
                {"role": "system", "content": "You are a conference program advisor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2048,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"LLM error: {e}")
        return "Failed to generate proposal."


def main():
    st.set_page_config(layout="wide")
    st.title("Conference Talk Proposal Generator")
    from config import use_local_llm
    if use_local_llm():
        st.caption("Running with local open-source LLM (USE_LOCAL_LLM / --local-llm).")
    st.markdown(
        "Combines historical talk data with real-time research to suggest unique proposals. "
        "Use as inspiration; submit your own original abstract."
    )

    try:
        if "cb_connection" not in st.session_state:
            with st.spinner("Connecting to Couchbase..."):
                st.session_state.cb_connection = CouchbaseConnection()
        cb = st.session_state.cb_connection

        user_query = st.text_area(
            "Enter your talk idea or topic:",
            placeholder="e.g., OpenTelemetry distributed tracing in serverless.",
            height=100,
        )

        if st.button("Generate Full Proposal", type="primary"):
            if not user_query:
                st.warning("Please enter your talk idea.")
                return

            adk_research_results = ""
            similar_talks = []

            with st.spinner("Step 1/3: Research agent (web trends)…"):
                try:
                    adk_research_results = run_adk_research(user_query)
                    st.success("Step 1: Research complete.")
                except Exception as e:
                    st.error(f"Research agent failed: {e}")
                    return

            with st.spinner("Step 2/3: Searching historical talks…"):
                similar_talks = cb.get_similar_talks(user_query)
                st.success("Step 2: Historical context loaded.")

            with st.spinner("Step 3/3: Generating proposal…"):
                if adk_research_results:
                    final_proposal = generate_talk_suggestion(
                        user_query, similar_talks, adk_research_results
                    )
                    st.success("Step 3: Proposal generated.")

                    st.divider()
                    st.subheader("Generated Talk Proposal")
                    st.markdown(final_proposal)
                    st.divider()

                    with st.expander("Real-time research (research agent)"):
                        st.markdown(adk_research_results)
                    with st.expander("Historical context (Couchbase)"):
                        if similar_talks:
                            st.json(similar_talks)
                        else:
                            st.info("No similar talks in the database.")
                else:
                    st.error("No research output; cannot generate proposal.")

    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Check .env (Couchbase, API keys) and refresh.")


if __name__ == "__main__":
    main()
