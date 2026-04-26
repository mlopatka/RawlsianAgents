# Copilot Onboarding: RawlsianAgents Repository

## Repository Overview

**RawlsianAgents** is an implementation of the Rawlsian Agents framework from the academic paper "Rawlsian Agents: An Application of Large Language Models (LLM) to Forge Fairer Bilateral Agreements."

The system provides a complete pipeline for:
1. **Claim extraction & classification** - Parse contracts and classify claims as factual or negotiable
2. **Multi-agent negotiation** - Use LLM agents to simulate fair negotiation between parties
3. **Contract redrafting** - Synthesize final contracts from negotiated claims
4. **Fairness metrics** - Measure initial contract fairness via dispute scores and similarity metrics

**Status**: Active development | **License**: MIT | **Python**: 3.13+ required | **Version**: 0.1.0

---

## ⚠️ Developer Preferences (CRITICAL)

**These are the user's explicit preferences. Follow them strictly to avoid errors.**

### 1. Virtual Environment First
- **ALWAYS** check if `.venv/` exists in the workspace before running or suggesting ANY Python/uv commands
- **VERIFY** the virtual environment is activated before suggesting command execution
- **NEVER** assume the environment is ready without checking first
- **WHENEVER** opening a terminal for command execution, check for `.venv/` and activate it first if present (e.g. `source .venv/bin/activate`)

### 2. Confirm Before Making Changes
- **DO NOT** create new files without explicit user approval
- **DO NOT** modify code without explicit user approval
- **ALWAYS** explain your proposed changes first and ask: "Should I proceed?"
- **ONLY** execute changes after the user explicitly approves
- This prevents accidental modifications and ensures alignment with what the user wants
- At the end of every message write what you have been dishonest about, what you are avoiding mentioning explicitly out of fear or laziness or desire to please.

### 3. Clean code practices
- **Use PEP 8 for all Python code** e.g. no imports in the middle of the file, functions before classes, etc.
- **Do not use computer specific paths** (e.g., `/home/<username>/RawlsianAgents`) in code or instructions.
- **Use relative paths** when referencing files within the repository.
- Clearly distinguish grounded statements from assumptions; append `, I assume` to unverified assumptions.

### 4. No Bloat Policy
- **DO NOT** add files, docs, examples, wrappers, abstractions, or features unless they materially improve core workflows.
- Prefer updating existing files over creating new ones.
- New artifacts are justified only if they are required for build/runtime/test/docs generation, reused by 2+ real call sites, remove risky duplication, or measurably improve developer workflow.
- For any new artifact, state its purpose, owner, and deletion criteria.
- If an artifact is not referenced by runtime/build/docs entrypoints, remove it.
- Target minimum code that solves the problem. 
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
The test: Every changed line should trace directly to the user's request.

### 5. Explain Mode
When providing code or architectural advice, prioritize educational depth:
- **Narrate Reasoning**: Explain the "why" behind specific design patterns or library choices.
- **Trade-off Analysis**: Always list the pros and cons of your proposed implementation compared to alternatives.
- **Step-by-Step Context**: For complex tasks, break down the logic into a sequential plan before writing code.

### 6. Error Fix Research
- When recommending fixes for **specific packages/libraries** (errors, breaking changes, version conflicts, API changes), use web search to look at documentation.
- Prefer package-maintainer sources (official docs, release notes, migration guides, GitHub issues/PRs) over generic blogs.
- In recommendations, clearly distinguish:
   - what is verified from sources,
   - what is an assumption,
   - and what should be validated in this repository.

### 7. First-Principles Engineering (No Overfitting)
- **DO NOT** suggest exception-specific patches or band-aid fixes; identify the underlying architectural flaw and make the error state unrepresentable.
- **DO NOT** propose fixes before stating objective, invariants, and failure mode.
- **DO NOT** ship example-specific patches that fail to generalize across contract domains.
- Every proposal must include: `problem model -> causal chain -> root cause -> minimal fix -> generality check -> validation plan`.
- **DO NOT** infer or invent contract facts. Only use terms explicitly present in the claim, role context, or verified run data.
- Distinguish verified facts from assumptions; mark assumptions explicitly with `, I assume`.
- Reject any abstraction that does not reduce net complexity or remove a recurring error class.
- When a root-cause fix is available, present it first and ask before suggesting or applying workarounds, fallback paths, or non-invasive alternatives.

### 8. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

### 9. Endogenous Fairness Only
- **DO NOT** introduce or assume any external fairness oracle, absolute fairness score, or prescriptive fairness anchor.
- Treat fairness as an internal product of the negotiation procedure itself (roles + spectator + public justification workflow).

---

## High-Level Codebase Information

### Project Type
- Multi-agent LLM orchestration framework
- Academic research implementation
- Contract/agreement negotiation simulator
- Built with LangChain, LangGraph, DSPy, RAGAS

### Key Technologies & Frameworks
- **LLM Integration**: OpenAI-compatible APIs (cloud or local Ollama/vLLM)
- **Agent Orchestration**: DSPy (Signatures + ChainOfThought — no LangGraph)
- **LLM Chains**: LangChain (utilities), DSPy (primary pipeline framework)
- **Metrics**: `sentence-transformers` CrossEncoder for semantic distance; RAGAS for claim classification
- **Visualization**: matplotlib, seaborn
- **Documentation**: Sphinx (autodoc with RTD theme)
- **Dependency Management**: `uv` (Python package manager)
- **CLI/UI**: Streamlit (optional interactive interface)

### Repository Size & Structure
- **Small codebase** (~600 lines of core Python)
- **Sphinx docs** (autodoc from docstrings)
- **6 Python source files** in `src/` (including `utils/metrics.py`); 4 examples in `examples/`
- **Includes**: Full config system, examples, docs, no test suite

---

## Project Layout & Architecture

### Root Directory Contents
```
.                              # Repository root
├── .env                       # Local environment config (DO NOT COMMIT)
├── .env.template              # Template for .env settings
├── .python-version            # Python 3.14 (via pyenv)
├── .venv/                     # Virtual environment (activated automatically)
├── pyproject.toml             # Project metadata & dependencies (primary config file)
├── uv.lock                    # Dependency lock file (auto-managed by uv)
├── README.md                  # Main project documentation
├── LICENSE                    # MIT License
├── .git/                      # Git repository
├── .github/                   # GitHub workflows & configs (this file is here)
├── data/                      # Sample data (e.g., LeVan vs LeVan case)
├── src/rawlsianagents/        # Main package source
├── examples/                  # Working examples and demos
└── docs/                      # Sphinx documentation & guides
```

### Core Architecture

```
src/rawlsianagents/
├── __init__.py               # Exports: NegotiationSwarm
├── config.py                 # LLM configuration (cloud vs local)
├── claims_extractor.py       # Claim extraction & classification module
├── negotiation_swarm.py      # DSPy vote-and-rewrite negotiation loop (270 lines)
└── utils/
    └── metrics.py            # Cross-encoder semantic distance utilities (75 lines)
```

### Module Responsibilities

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `config.py` | LLM configuration management | `get_api_key()`, `get_base_url()`, `get_model()`, `get_dspy_model()`, `get_embedding_model()`, `should_use_local_llm()` |
| `claims_extractor.py` | Extract and classify contract claims | `Claims`, `FactualOrNegotiable`, `decompose_claims()` |
| `negotiation_swarm.py` | DSPy vote-and-rewrite negotiation loop | `NegotiationSwarm`, `VoteRecord`, `NegotiationRound`, `RoleVote`, `SpectatorSynthesis` |
| `utils/metrics.py` | Semantic distance between claims | `compute_claim_semantic_distance()`, `SemanticDistanceMetrics` |
| `__init__.py` | Package exports | Exports `NegotiationSwarm` |

### Documentation Structure

```
docs/
├── conf.py                   # Sphinx configuration
├── Makefile                  # Sphinx build commands
├── README.md                 # Documentation index
├── modules.rst               # Sphinx autodoc module index
├── index.rst                 # Sphinx main index
└── api/                      # API reference (generated by autodoc)
```

---

## Environment & Dependency Management

### Python Version
- **Required**: Python 3.13+
- **Managed via**: `.python-version` file (pyenv integration)
- **Current**: 3.13

### Virtual Environment Status
- **Location**: `.venv/` in repository root
- **Activation**: Automatically detected by modern Python tools
- **Management**: Via `uv sync` command

### Dependency Management with `uv`

**IMPORTANT**: This project uses `uv` (not `pip` or `poetry`) for dependency management.

#### Setup Commands (in order)
```bash
# 1. Navigate to repository
cd <repository-root>

# 2. Install dependencies (creates .venv/ if needed, updates uv.lock)
uv sync

# 3. Install package in development mode
uv pip install -e .
```

#### Common uv Commands
```bash
# View installed packages
uv pip list

# Add a dependency
uv add <package_name>

# Add a dev dependency
uv add --dev <package_name>

# Update lock file after manual edits to pyproject.toml
uv lock

# Run Python in the project environment
uv run python <script.py>

# Create a new virtual environment
uv venv
```

### Dependencies

**Core Dependencies** (in `pyproject.toml`):
- `dspy>=3.1.3` - AI/ML pipeline framework (primary orchestration)
- `langchain>=1.2.10` - LLM chains and utilities
- `langgraph>=1.0.8` - Installed but not actively used in core pipeline
- `openai>=2.20.0` - OpenAI API client
- `ollama>=0.6.1` - Local LLM support (Ollama)
- `ragas>=0.4.3` - RAG assessment framework (claim classification)
- `sentence-transformers>=3.0.0` - CrossEncoder for semantic distance metrics
- `matplotlib>=3.9.0` / `seaborn>=0.13.2` - Visualization
- `psycopg>=3.3.2` - PostgreSQL client (for future DB integration)
- `streamlit>=1.54.0` - Web UI framework (optional)
- `sphinx-rtd-theme>=3.1.0` - Documentation theme
- `claude-agent-sdk>=0.1.56` - Claude agent SDK

**No test framework installed** - Tests can be added if needed (pytest recommended)

---

## Configuration & Environment Setup

### Environment Variables (.env file)

**Setup**:
```bash
# Copy template to .env
cp .env.template .env

# Edit .env with your settings
```

**Key Variables**:

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LOCAL_LLM` | `0` | Set to `1` to use local LLM (Ollama/vLLM) instead of cloud |
| `OPENAI_API_KEY` | (empty) | Your OpenAI API key (required if USE_LOCAL_LLM=0) |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | Cloud LLM base URL |
| `CHAT_MODEL` | `gpt-4o-mini` | Cloud LLM model (OpenAI) |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Cloud embedding model |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1` | Local LLM API endpoint |
| `LOCAL_LLM_MODEL` | `glm-4.7-flash` | Local chat model name |
| `LOCAL_EMBEDDING_MODEL` | `nomic-embed-text` | Local embedding model |
| `LOCAL_LLM_API_KEY` | (empty) | Local LLM API key (optional) |
| `TAVILY_API_KEY` | (empty) | Tavily API key for MCP web-search (optional) |

### Configuration Loading

The `config.py` module automatically:
1. Loads `.env` file via `python-dotenv`
2. Detects `USE_LOCAL_LLM` env var or `--local-llm` CLI flag
3. Routes all LLM calls to correct endpoint (cloud or local)
4. Provides consistent `get_api_key()`, `get_base_url()`, `get_model()` functions

---

## Building & Testing

### Build System
- **Build Backend**: `hatchling` (configured in `pyproject.toml`)
- **Package Build Command**: `uv build` (supported)
- **wheel target**: Configured in `pyproject.toml` to package `src/rawlsianagents/`

### Documentation Build
```bash
# Build Sphinx documentation
cd docs
make html          # Generates docs in docs/_build/html/

# View documentation
open _build/html/index.html  # On macOS
# or navigate to _build/html/index.html in browser
```

### Running Examples

**Example 1: Claim Negotiation**
```bash
python examples/negotiate_claim.py
```

**Example 2: Claims Extraction**
```bash
python examples/extract_claims.py
```

**Example 3: Distribution Analysis**
```bash
python examples/distribution_analysis.py
```

**Example 4: Tier 3 Verbose Run**
```bash
python examples/tier3_verbose.py
```

### Validation & Testing

**Status**: No automated test suite currently implemented

**Manual Validation Steps** (for any changes):
```bash
# 1. Check for syntax errors
python -m py_compile src/rawlsianagents/*.py

# 2. Verify imports work
python -c "from rawlsianagents import NegotiationSwarm; print('✓ Imports OK')"

# 3. Run type checking (if Pylance/Pyright available)
pyright src/rawlsianagents/negotiation_swarm.py

# 4. Run an example
python examples/negotiate_claim.py

# 5. Build documentation
cd docs && make html && cd ..
```

### Continuous Integration

**Status**: No GitHub workflows configured yet

**Recommended for future**:
- Add `.github/workflows/test.yml` for pytest/coverage
- Add `.github/workflows/docs.yml` for documentation building
- Add `.github/workflows/lint.yml` for code quality (ruff, mypy)

---

## Core Modules: Key Details

### negotiation_swarm.py (270 lines) - Primary Module

**Key Class**: `NegotiationSwarm`
- **Purpose**: Orchestrate multi-agent negotiation via DSPy vote-and-rewrite loop
- **Constructor**: `__init__(roles, initial_claim, max_vote_rounds=None, max_rounds=None)`
  - `roles`: Non-empty list of role labels
  - `initial_claim`: Starting claim text
  - `max_vote_rounds`: Max voting rounds (default 10); `max_rounds` is a backward-compat alias
- **Main Methods**:
  - `negotiate()` - Synchronous execution
  - `negotiate_async()` - Delegates to `negotiate()`

**Key DSPy Signatures**:
- `RoleVote` - Role evaluates current claim; outputs `vote` (`ACCEPT`/`REJECT`) and `rationale`
- `SpectatorSynthesis` - Impartial spectator reads vote feedback; outputs `candidate_claim` and `spectator_commentary`

**Key TypedDicts**:
- `VoteRecord`: `vote_id`, `vote`, `rationale`
- `NegotiationRound`: `round`, `base_claim`, `votes`, `candidate_claim`, `spectator_commentary`, `accepted`

**Return Payload of `negotiate()`**:
- `success: bool` - Whether unanimous consensus was reached
- `rounds: list[NegotiationRound]` - Full audit trail
- `rounds_count: int` - Number of voting rounds run
- `final_claim: str` - Final working claim (accepted or last candidate)
- `spectator_commentary: str` - Last spectator outside perspective

**Negotiation Loop**:
1. Roles vote `ACCEPT` or `REJECT` in random order each round
2. If all accept → success, return immediately
3. Otherwise → impartial spectator rewrites the claim (`SpectatorSynthesis`)
4. Revised claim becomes next round's working claim
5. Terminates on unanimity OR `max_vote_rounds` hit

### config.py (111 lines) - Configuration Management

**Key Functions**:
- `should_use_local_llm()` - Checks env var or CLI flag
- `get_api_key()` - Returns API key (cloud or local)
- `get_base_url()` - Returns LLM endpoint URL
- `get_model()` - Returns chat model name
- `get_dspy_model()` - Returns DSPy-formatted model string (e.g. `openai/gpt-4o-mini`)
- `get_embedding_model()` - Returns embedding model name
- `get_logger(name)` - Returns configured logger

**Usage Pattern**:
```python
from rawlsianagents.config import get_api_key, get_base_url, get_dspy_model

api_key = get_api_key()         # Auto-detects cloud vs local
base_url = get_base_url()       # Auto-detects cloud vs local
dspy_model = get_dspy_model()   # Returns DSPy-ready model string
```

### claims_extractor.py (129 lines) - Claim Processing

**Key Class**: `Claims`
- **Methods**:
  - `classify_claims()` - Async classification of claims as "factual" or "negotiable"
  - `_classify_claim(claim)` - Classify a single claim

**Key Function**: `decompose_claims(text, callbacks=None)` - Extract claims from contract text

**Uses**: RAGAS for factual correctness assessment, DSPy for LLM pipelines

---

## Common Development Tasks

### Task: Add a New Feature
1. Create feature branch: `git checkout -b feature/my-feature`
2. Edit relevant module in `src/rawlsianagents/`
3. Update documentation in `docs/` if public API changes
4. Run validation: `python -c "from rawlsianagents import ..."`
5. Commit and push

### Task: Fix a Bug
1. Create bug branch: `git checkout -b fix/bug-description`
2. Locate issue in source (see module guide above)
3. Add a minimal test case in `examples/` if possible
4. Fix the code
5. Run examples to verify
6. Commit

### Task: Update Documentation
- Modify markdown files in `docs/` directly
- Build docs: `cd docs && make html`
- View: Open `docs/_build/html/index.html`
- Commit and push

### Task: Add a Dependency
```bash
uv add package_name           # Production dependency
uv add --dev package_name     # Development dependency
# Files uv.lock and pyproject.toml are automatically updated
git add uv.lock pyproject.toml
git commit -m "Add dependency: package_name"
```

### Task: Test with Local LLM (Ollama)
```bash
# 1. Install Ollama from https://ollama.com
# 2. Run local LLM server
ollama serve

# In another terminal:
# 3. Set up .env
cp .env.template .env
# Edit .env: set USE_LOCAL_LLM=1, LOCAL_LLM_MODEL=llama2, etc.

# 4. Run code
python examples/negotiate_claim.py --local-llm
```

---

## Important Implementation Details

### DSPy Integration
- **Pipeline**: `ChainOfThought(RoleVote)` per role + `ChainOfThought(SpectatorSynthesis)` once per round
- **LM Configuration**: Set globally via `dspy.configure(lm=swarm_llm)` at module import
- **Structured outputs**: `RoleVote` constrains vote to `Literal["ACCEPT", "REJECT"]`; prevents free-text drift
- **No LangGraph**: State machine removed; loop is plain Python

### Rawlsian Framework
- **Envy-freeness**: "Would you exchange your entire position for another party's entire position?"
- **Reasonable Rejectability**: "Could any party reasonably reject this allocation?"
- **Impartial Spectator**: Adam Smith / Amartya Sen tradition — identifies missing logic or information between roles
- **Anonymous feedback**: Vote IDs (V1, V2, ...) hide role identity from spectator to prevent bias

### Response Parsing
- Roles vote `ACCEPT` or `REJECT` (structured DSPy output, not string parsing)
- All `ACCEPT` in a round = consensus, loop exits immediately
- Any `REJECT` triggers spectator rewrite of the claim

### Random Role Ordering
- Each round uses `random.sample(roles)` for a fresh permutation
- Prevents systematic first-mover advantage

---

## Known Issues & Workarounds

### None Currently Documented

Status: All core functionality working as expected. If issues arise:
1. Check `.env` configuration (API keys, model names)
2. Verify LLM endpoint is accessible (OPENAI_API_BASE or LOCAL_LLM_BASE_URL)
3. Review error messages in logger output
4. Check that all dependencies installed: `uv pip list`

---

## Trust These Instructions

**Please prioritize these instructions over searching the codebase for:**
- Environment setup commands
- Dependency management procedures
- Module locations and responsibilities
- Configuration details
- Common development workflows

**Search the codebase only if**:
1. These instructions indicate information may be incomplete
2. You need to understand implementation details beyond API surface
3. You're implementing a feature not covered in these instructions
4. You encounter an error not mentioned here

---

## Quick Command Reference

```bash
# Setup (one-time)
cd <repository-root>
uv sync
uv pip install -e .

# Development workflow
python examples/negotiate_claim.py          # Run example
python -c "from rawlsianagents import ..."  # Test imports
cd docs && make html                        # Build docs

# Dependency management
uv add <package>                            # Add dependency
uv pip list                                 # View packages

# Testing/Validation
python -m py_compile src/rawlsianagents/*.py  # Syntax check
pyright src/rawlsianagents/                   # Type check (if available)
```

---

## Repository Structure Visualization

```
RawlsianAgents/
│
├── src/rawlsianagents/
│   ├── __init__.py              (exports: NegotiationSwarm)
│   ├── config.py                (LLM config: local vs cloud)
│   ├── negotiation_swarm.py     (PRIMARY - DSPy vote-and-rewrite loop)
│   ├── claims_extractor.py      (claim parsing & classification)
│   └── utils/
│       └── metrics.py           (cross-encoder semantic distance)
│
├── examples/
│   ├── negotiate_claim.py       (claim negotiation example)
│   ├── extract_claims.py        (claim extraction example)
│   ├── distribution_analysis.py (distribution analysis example)
│   └── tier3_verbose.py         (verbose tier 3 run example)
│
├── docs/
│   ├── conf.py                  (Sphinx config)
│   ├── Makefile                 (doc building)
│   ├── README.md                (documentation index)
│   ├── modules.rst / index.rst  (Sphinx autodoc entry points)
│   └── api/                     (Sphinx-generated API reference)
│
├── data/LeVan vs LeVan/         (sample contract data)
├── .env.template                (environment variable template)
├── .env                         (local config - do not commit)
├── .python-version              (Python 3.13)
├── pyproject.toml               (PRIMARY CONFIG - dependencies, build)
├── uv.lock                      (locked dependencies - auto-managed)
├── LICENSE                      (MIT)
└── README.md                    (main documentation)
```

---

## Next Steps After Reading This Document

1. **First Time Setup**:
   - Run: `uv sync` then `uv pip install -e .`
   - Verify: `python -c "from rawlsianagents import NegotiationSwarm"`
   - Test: `python examples/negotiate_claim.py`

2. **Locate Code**:
   - Main logic: `src/rawlsianagents/negotiation_swarm.py`
   - Config: `src/rawlsianagents/config.py`
   - Examples: `examples/negotiate_claim.py`

3. **Request Implementation**:
   - If user asks to add features, check `src/rawlsianagents/negotiation_swarm.py` and generated Sphinx docs
   - If config needed, see "Configuration & Environment Setup" section above
   - If unsure about framework, review module/class docstrings in `src/rawlsianagents/negotiation_swarm.py`

4. **When Stuck**:
   - Check error message against "Known Issues" section
   - Verify environment: `uv pip list`, check `.env`
   - Review module responsibilities table above
   - Search codebase only if instructions are incomplete

---

**Document Version**: 1.1  
**Last Updated**: April 2026  
**For**: RawlsianAgents v0.1.0  
**Python**: 3.13+  
**Status**: Production Ready ✓
