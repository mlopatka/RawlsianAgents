# Agentic Workflow – Conference Talk Abstract Generator

A multi-stage agentic pipeline for generating conference talk proposals, combining **data collection**, **vector storage**, and **RAG** with a **research agent** (Google ADK). Use this skeleton to plug in your own data sources and LLM providers.

## Architecture Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  1. Extract URLs    │ ──► │  2. Crawl & Store   │ ──► │  3. Embeddings       │
│  extract_events.py  │     │  couchbase_utils.py │     │  embeddinggeneration │
└─────────────────────┘     │  crawl_talks.py     │     └──────────┬──────────┘
                            └─────────────────────┘                │
                                                                   ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  5. Streamlit App   │ ◄── │  4. ADK Research    │     │  Couchbase (vector  │
│  talk_suggestions_  │     │  adk_research_agent │     │  search)            │
│  app.py             │     └─────────────────────┘     └─────────────────────┘
└─────────────────────┘
```

1. **Data collection** – Extract event/talk URLs from HTML (or other sources).
2. **Data processing** – Crawl pages or load JSON; parse and store in Couchbase.
3. **Vector storage** – Generate embeddings and index for semantic search.
4. **Research agent** – ADK pipeline (parallel search tools → summary → analysis).
5. **RAG app** – Streamlit UI: research + vector search → final proposal generation.

## Prerequisites

- Python 3.10+
- Couchbase Server with Vector Search (or swap for another vector DB)
- OpenAI-compatible API (e.g. Nebius AI) for embeddings and chat **or** a local open-source LLM (see below)
- Optional: Exa / Tavily / Linkup API keys for the research agent

### Optional: local open-source LLM (Hugging Face / Ollama)

You can run the pipeline with a **local** OpenAI-compatible server (e.g. [Ollama](https://ollama.com), vLLM, Hugging Face Inference) instead of a cloud API.

- **Env flag:** set `USE_LOCAL_LLM=1` (or `true` / `yes`) in `.env`.
- **CLI flag:** run the Streamlit app with `--local-llm`:
  ```bash
  streamlit run talk_suggestions_app.py -- --local-llm
  ```

Configure in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API base (Ollama default) |
| `LOCAL_LLM_MODEL` | `llama3.2` | Chat model name (Ollama pull name or your server’s model id) |
| `LOCAL_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model (Ollama or local embed server) |
| `LOCAL_LLM_API_KEY` | (empty) | Optional; Ollama ignores it |

**Example (Ollama):**

```bash
# Install Ollama, then e.g.:
ollama pull llama3.2
ollama pull nomic-embed-text

# .env
USE_LOCAL_LLM=1
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.2
LOCAL_EMBEDDING_MODEL=nomic-embed-text
```

**Note:** Local embedding models often use different dimensions (e.g. 768 for `nomic-embed-text`) than cloud models (e.g. 4096). Create your Couchbase vector index with the correct `dims` for the model you use.

## Pipeline Steps

### Step 1: URL extraction (`extract_events.py`)

Read HTML from stdin, extract event URLs, merge into `event_urls.txt`.

```bash
python extract_events.py < schedule.html
```

### Step 2: Crawl and store (`couchbase_utils.py`)

Read URLs from `event_urls.txt`, crawl with AsyncWebCrawler, parse HTML, store in Couchbase.

```bash
python couchbase_utils.py
```

### Step 3: Optional JSON import (`crawl_talks.py`)

Import pre-crawled talks from `talk_results1.json` into Couchbase.

```bash
python crawl_talks.py
```

### Step 4: Embeddings (`embeddinggeneration.py`)

Load documents from Couchbase, compute embeddings, write back and use for vector search.

```bash
python embeddinggeneration.py
```

### Step 5: RAG app (`talk_suggestions_app.py`)

Run the Streamlit app: research agent + vector search → final talk proposal.

```bash
streamlit run talk_suggestions_app.py
```

With a local LLM (optional):

```bash
streamlit run talk_suggestions_app.py -- --local-llm
```

## Environment

Copy `.env.example` to `.env` and set:

- `CB_*` – Couchbase connection, bucket, collection, search index
- `NEBIUS_API_KEY`, `NEBIUS_API_BASE` (or your OpenAI-compatible endpoint)
- Optional: `USE_LOCAL_LLM=1` and `LOCAL_LLM_*` for a local open-source LLM (Ollama / Hugging Face)
- Optional: `EXA_API_KEY`, `TAVILY_API_KEY`, `LINKUP_API_KEY` for the research agent

## File layout

```
proposal/
├── README.md
├── requirements.txt
├── .env.example
├── config.py              # LLM config (cloud vs local)
├── extract_events.py      # URL extraction from HTML
├── couchbase_utils.py     # Crawl talks + store in Couchbase
├── crawl_talks.py         # JSON → Couchbase import
├── embeddinggeneration.py # Generate and store embeddings
├── adk_research_agent.py  # ADK research agent (tools + pipeline)
├── talk_suggestions_app.py # Streamlit RAG app
├── event_urls.txt         # (generated) extracted URLs
└── talk_results1.json     # (optional) pre-crawled data
```

## References

Template: [awesome-ai-apps / conference_talk_abstract_generator](https://github.com/Arindam200/awesome-ai-apps/tree/main/advance_ai_agents/conference_talk_abstract_generator)
