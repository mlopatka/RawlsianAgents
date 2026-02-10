# Rawlsian Agents: LLM-Based Contract Negotiation & Fairness Assessment

An implementation of **Rawlsian Agents** based on [Rawlsian Agents: An Application of Large Language Models (LLM) to Forge Fairer Bilateral Agreements](https://link.springer.com/chapter/10.1007/978-3-032-15632-7_1). This system uses LLMs to analyze, negotiate, and redraft contracts through multi-agent simulated negotiation, measuring initial contract fairness via negotiation metrics.

## Architecture Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  1. Claim           │ ──► │  2. Negotiation     │ ──► │  3. Contract        │
│  Extraction &       │     │  Simulation         │     │  Drafting           │
│  Classification     │     │  (Multi-Agent)      │     │  (Final Output)     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         │                           │                            │
         │                           │                            ▼
    Factual vs.               Amendment Rounds          ┌─────────────────────┐
    Negotiable                Per Claim Tracking        │  4. Fairness Metrics│
    Claims                    Dispute Score             │  - Dispute Score    │
                                                        │  - BERT Similarity  │
                                                        └─────────────────────┘
```

### Pipeline Stages

1. **Claim Extraction & Classification** – Parse initial contract and classify claims as *factual* (immutable) or *negotiable* (subject to discussion).
2. **Negotiation Simulation** – For each negotiable claim:
   - Agents simulate parties to the contract
   - Propose amendments or new claims
   - Track negotiation rounds per claim
3. **Contract Drafting** – Synthesize factual claims + revised negotiable claims into a final contract.
4. **Fairness Assessment** – Compute metrics:
   - **Dispute Score**: Total rounds normalized by # of negotiable claims (proxy for initial injustice/ambiguity)
   - **Per-Claim Dispute Score**: Rounds per claim (highlights most contentious clauses)
   - **BERT Score**: Semantic similarity between original and final contracts (magnitude of required changes)

## Prerequisites

- Python 3.10+
- OpenAI-compatible API (e.g. OpenAI, Nebius AI) for chat **or** a local open-source LLM (see below)

## Dependency Management (uv)

This project uses [pyproject.toml](pyproject.toml) and [uv.lock](uv.lock) for dependency management.

Install dependencies:

```bash
uv sync
```

Add a dependency:

```bash
uv add <package>
```

Add a dev dependency:

```bash
uv add --dev <package>
```

Update the lockfile after manual edits to [pyproject.toml](pyproject.toml):

```bash
uv lock
```

### Optional: Local Open-Source LLM (Ollama / vLLM)

Run the pipeline with a **local** OpenAI-compatible server (e.g. [Ollama](https://ollama.com), vLLM, Hugging Face Inference) instead of a cloud API.

- **Env flag:** set `USE_LOCAL_LLM=1` (or `true` / `yes`) in `.env`.
- **CLI flag:** run scripts with `--local-llm`:
  ```bash
  python negotiate_claims.py --local-llm ...
  ```

Configure in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible API base (Ollama default) |
| `LOCAL_LLM_MODEL` | `glm-4.7-flash` | Chat model name (Ollama pull name or your server's model id) |
| `LOCAL_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model (Ollama or local embed server) |
| `LOCAL_LLM_API_KEY` | (empty) | Optional; Ollama ignores it |

**Example (Ollama):**

First, install Ollama:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Then pull the models:
```bash
ollama pull glm-4.7-flash
ollama pull nomic-embed-text
```

Update `.env`:
```bash
USE_LOCAL_LLM=1
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=glm-4.7-flash
LOCAL_EMBEDDING_MODEL=nomic-embed-text
```

## Usage

### Step 1: Extract and Classify Claims

```bash
python extract_claims.py --input contract.txt --output claims.json
```

Parses the input contract and outputs a JSON with claims tagged as `factual` or `negotiable`.

### Step 2: Run Negotiation Simulation

```bash
python negotiate_claims.py --input claims.json --output negotiated_claims.json
```

Simulates multi-agent negotiation for each negotiable claim. Tracks amendment rounds and outputs revised claims.

### Step 3: Draft Final Contract

```bash
python draft_contract.py --factual claims.json --negotiated negotiated_claims.json --output final_contract.txt
```

Combines factual claims with negotiated revisions to produce the final contract.

### Step 4: Compute Fairness Metrics

```bash
python compute_metrics.py --original contract.txt --final final_contract.txt --negotiation negotiated_claims.json
```

Outputs:
- Total negotiation rounds
- Per-claim dispute scores
- Normalized dispute score
- BERT similarity score

### Interactive UI (Optional)

Launch the Streamlit app to upload a contract and receive a fairness report.
The app runs the full pipeline end-to-end and returns the Dispute Score,
per-claim dispute breakdown, and BERT similarity summary.

```bash
streamlit run app.py
```

With a local LLM:

```bash
streamlit run app.py -- --local-llm
```

## Environment

Copy [.env.template](.env.template) to `.env` and fill in your values:

```bash
cp .env.template .env
```

Required:
- `OPENAI_API_KEY` for OpenAI-compatible endpoint

Optional:
- `USE_LOCAL_LLM=1` and `LOCAL_LLM_*` for a local open-source LLM (Ollama / vLLM / Hugging Face Inference)

## File Layout

```
RawlsianAgents/
├── README.md
├── pyproject.toml         # Dependencies (uv)
├── .env.template          # Environment template
├── src/
│   └── rawlsianagents/
│       ├── config.py              # LLM config (cloud vs local)
│       ├── extract_claims.py      # Claim extraction & classification
│       ├── negotiate_claims.py    # Multi-agent negotiation simulation
│       ├── draft_contract.py      # Final contract synthesis
│       └── compute_metrics.py     # Fairness/injustice metrics
├── app.py                 # Streamlit UI (optional)
└── tests/                 # Unit tests
```

## Key Concepts

### Fairness Metrics

- **Dispute Score** = `total_rounds / num_negotiable_claims`  
  Higher scores indicate more initial injustice or ambiguity.
  
- **Per-Claim Dispute Score** = `rounds_for_claim_i`  
  Identifies the most contentious clauses.

- **BERT Score** = `semantic_similarity(original_contract, final_contract)`  
  Measures magnitude of required changes (lower = more revisions needed).

### Why Rawlsian?

Based on John Rawls' principles of justice, the system simulates negotiation behind a "veil of ignorance" where agents optimize for fairness rather than self-interest, converging toward more equitable contract terms.

## References

- [Rawlsian Agents: An Application of Large Language Models (LLM) to Forge Fairer Bilateral Agreements](https://link.springer.com/chapter/10.1007/978-3-032-15632-7_1)
