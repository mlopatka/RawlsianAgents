# Rawlsian Agents: LLM-Based Contract Negotiation & Fairness Assessment

An implementation of **Rawlsian Agents** based on [Rawlsian Agents: An Application of Large Language Models (LLM) to Forge Fairer Bilateral Agreements](https://link.springer.com/chapter/10.1007/978-3-032-15632-7_1) and [its original codebase](https://github.com/aegerita/Rawlsian-Agents). This system uses LLMs to analyze, discuss, and redraft contracts through multi-agent simulated debate, measuring initial contract fairness via negotiation metrics.

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

1. **Claim Extraction & Classification** – Parse contract text and classify claims as *factual* or *negotiable*.
2. **Negotiation Swarm** – Run multi-role negotiation over a claim until all roles are satisfied or `max_rounds` is reached:
  - Role nodes revise the latest claim and append adjustment notes
  - Impartial spectator appends neutral perspective suggestions
  - Round reset node restarts role turn-tracking between rounds
3. **Negotiation Output** – Return the final claim plus traceable negotiation artifacts:
  - `final_claim`, `adjustment_notes`, `satisfied_roles`
  - `rounds`, `agreement_count`, `success (all roles satisfied)`

## Prerequisites

- Python 3.14+
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

### Installing the Package

After running `uv sync`, install the package in development mode to make `rawlsianagents` importable:

```bash
uv pip install -e .
```

## View Documentation Locally

Build the Sphinx docs:

```bash
uv run make -C docs html
```

- The `html` target depends on `apidoc` (`html: apidoc`), so it runs first.
- `apidoc` calls `sphinx-apidoc` to regenerate API `.rst` stubs in `docs/api` from `src/rawlsianagents`.
- This keeps API pages aligned with the current Python modules before HTML generation.

Then either open the generated file directly:

- `docs/_build/html/index.html`

Or serve the docs folder locally with Python:

```bash
cd docs/_build/html
python -m http.server 8000
```

If you want to regenerate API stubs manually only:

```bash
uv run sphinx-apidoc --force --no-toc --separate -o docs/api src/rawlsianagents
```

Open:

- `http://localhost:8000`

### Optional: Local Open-Source LLM (Ollama / vLLM)

Run the negotiation examples with a **local** OpenAI-compatible server (e.g. [Ollama](https://ollama.com), vLLM, Hugging Face Inference) instead of a cloud API.

- Set `USE_LOCAL_LLM=1` (or `true` / `yes`) in `.env`.
- Then run the examples normally (for example, `python examples/negotiate_claim.py`).

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

### Quick Start: Negotiation Swarm

The `NegotiationSwarm` module provides a simple way to negotiate claims among multiple parties:

```python
from rawlsianagents import NegotiationSwarm

# Define roles and initial claim
roles = ["LeVan family", "bride", "groom", "potential children"]
initial_claim = (
  "The marriage contract excludes all of the husband's business interests "
  "from net family property and limits the wife's right to support."
)

# Create and run negotiation
swarm = NegotiationSwarm(
    roles=roles,
    initial_claim=initial_claim,
  max_rounds=20,
)

result = swarm.negotiate()
print(f"Final claim: {result['final_claim']}")
print(f"Completed in {result['rounds']} rounds")
print(f"Success: {result['success']}")
print(f"Satisfied roles: {result['satisfied_roles']}")
```

See [examples/negotiate_claim.py](examples/negotiate_claim.py) for more examples. For generated API docs, build Sphinx docs and open `docs/_build/html/index.html`.

### Current NegotiationSwarm Behavior

- Constructor: `NegotiationSwarm(roles, initial_claim, max_rounds=20)`
- Role nodes evaluate and potentially revise `latest_claim` using DSPy `RoleEvaluation`
- Satisfaction is tracked in `satisfied_roles` and role participation in `roles_spoken_this_round`
- After each full round-robin, spectator appends neutral suggestions to `adjustment_notes`
- A dedicated `reset_round` node resets round bookkeeping before the next round
- Negotiation ends when all roles are satisfied or `max_rounds` is reached

Return payload includes:

- `original_claim`
- `final_claim`
- `adjustment_notes`
- `rounds`
- `agreement_count`
- `success`
- `satisfied_roles`

### Pipeline Usage

### Run Claim Extraction Example

```bash
python examples/extract_claims.py
```

Runs the extraction/classification workflow over the included sample inputs.

### Run Negotiation Swarm Example

```bash
python examples/negotiate_claim.py
```

Runs the current `NegotiationSwarm` flow and prints the final claim plus satisfaction map.

### Output from NegotiationSwarm

`negotiate()` and `negotiate_async()` return:

- `original_claim`
- `final_claim`
- `adjustment_notes`
- `rounds`
- `agreement_count`
- `success`
- `satisfied_roles`

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
├── data/                  # Sample agreements and inputs
├── src/
│   └── rawlsianagents/
│       ├── config.py              # LLM config (cloud vs local)
│       ├── claims_extractor.py    # Claim extraction & classification
│       ├── negotiation_swarm.py   # Multi-agent negotiation swarm
│       └── __init__.py            # Public package exports
├── examples/
│   ├── extract_claims.py          # Example: Extract claims
│   └── negotiate_claim.py         # Example: Negotiation swarm
├── docs/
│   ├── index.rst                  # Sphinx entrypoint
│   ├── modules.rst                # API module index
│   ├── api/                       # API rst pages
│   └── ...
└── uv.lock                # Locked dependency graph
```

## Key Concepts

### Fairness Metrics

- **Dispute Score** = `total_rounds / num_negotiable_claims`  
  Higher scores indicate more initial injustice or ambiguity.
  
- **Per-Claim Dispute Score** = `rounds_for_claim_i`  
  Identifies the most contentious clauses.

- **BERT Score** = `semantic_similarity(original_contract, final_contract)`  
  Measures magnitude of required changes (lower = more revisions needed).

## References

- [Rawlsian Agents: An Application of Large Language Models (LLM) to Forge Fairer Bilateral Agreements](https://link.springer.com/chapter/10.1007/978-3-032-15632-7_1)
