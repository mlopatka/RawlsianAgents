# Copilot Onboarding: RawlsianAgents Repository

## Repository Overview

**RawlsianAgents** is an implementation of the Rawlsian Agents framework from the academic paper "Rawlsian Agents: An Application of Large Language Models (LLM) to Forge Fairer Bilateral Agreements."

The system provides a complete pipeline for:
1. **Claim extraction & classification** - Parse contracts and classify claims as factual or negotiable
2. **Multi-agent negotiation** - Use LLM agents to simulate fair negotiation between parties
3. **Contract redrafting** - Synthesize final contracts from negotiated claims
4. **Fairness metrics** - Measure initial contract fairness via dispute scores and similarity metrics

**Status**: Active development | **License**: MIT | **Python**: 3.14+ required | **Version**: 0.1.0

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
- **Do not use computer specific paths** (e.g., `/home/<username>/RawlsianAgents`) in code or instructions
- **Use relative paths** when referencing files within the repository
- You must clearly indicate what part of what you say is assumption, and which part is grounded.
You must add ', I assume' after every unverified assumption to make explicitely clear what is an assumption, and what is a verified fact.

### 4. No Bloat Policy
- **DO NOT** add files, docs, examples, wrappers, abstractions, or features unless they materially improve core workflows (run, debug, extend, document)
- A change is allowed only if it is at least one of the following:
   - Required for build/runtime/test/docs generation
   - Reused by 2+ real call sites
   - Removes duplicated logic that creates maintenance risk
   - Measurably improves developer workflow (setup, debugging, onboarding)
- **PREFER** updating existing files over creating new files
- For any new artifact, state: purpose, owner, and deletion criteria
- If an artifact is not referenced by runtime/build/docs entrypoints, remove it

### 5. Explain Mode
When providing code or architectural advice, prioritize educational depth:
- **Narrate Reasoning**: Explain the "why" behind specific design patterns or library choices.
- **Insight Blocks**: Include brief "Pro Tips" or background info on best practices within your response.
- **Trade-off Analysis**: Always list the pros and cons of your proposed implementation compared to alternatives.
- **Step-by-Step Context**: For complex tasks, break down the logic into a sequential plan before writing code.

### 6. Package Fix Research (Tavily)
- When recommending fixes for **specific packages/libraries** (errors, breaking changes, version conflicts, API changes), use **Tavily search** first.
- Prefer package-maintainer sources (official docs, release notes, migration guides, GitHub issues/PRs) over generic blogs.
- In recommendations, clearly distinguish:
   - what is verified from sources,
   - what is an assumption,
   - and what should be validated in this repository.
---

## High-Level Codebase Information

### Project Type
- Multi-agent LLM orchestration framework
- Academic research implementation
- Contract/agreement negotiation simulator
- Built with LangChain, LangGraph, DSPy, RAGAS

### Key Technologies & Frameworks
- **LLM Integration**: OpenAI-compatible APIs (cloud or local Ollama/vLLM)
- **Agent Orchestration**: LangGraph (state graph-based agents)
- **LLM Chains**: LangChain, DSPy (AI/ML pipeline framework)
- **Metrics**: RAGAS (Retrieval-Augmented Generation Assessment)
- **Documentation**: Sphinx (autodoc with RTD theme)
- **Dependency Management**: `uv` (Python package manager)
- **CLI/UI**: Streamlit (optional interactive interface)

### Repository Size & Structure
- **Small-to-medium codebase** (~2,500 lines of core Python)
- **Well-documented**: 13 markdown documentation files + Sphinx docs
- **8 Python source files** (6 in src/, 2 in examples/)
- **Includes**: Full config system, examples, docs, tests setup

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
├── __init__.py               # Exports: NegotiationSwarm, NegotiationState
├── config.py                 # LLM configuration (cloud vs local)
├── claims_extractor.py       # Claim extraction & classification module
├── negotiation_swarm.py      # Multi-agent negotiation orchestration (450 lines)
└── utils/                    # Utility functions (currently empty, reserved)
```

### Module Responsibilities

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| `config.py` | LLM configuration management | `get_api_key()`, `get_base_url()`, `get_model()`, `should_use_local_llm()` |
| `claims_extractor.py` | Extract and classify contract claims | `Claims`, `FactualOrNegotiable`, `decompose_claims()` |
| `negotiation_swarm.py` | Multi-agent negotiation via LangGraph | `NegotiationSwarm`, `NegotiationState`, `_create_role_node()`, `_create_spectator_node()` |
| `__init__.py` | Package exports | Exports `NegotiationSwarm`, `NegotiationState` |

### Documentation Structure

```
docs/
├── conf.py                   # Sphinx configuration
├── Makefile                  # Sphinx build commands
├── README.md                 # Documentation index
├── negotiation_swarm.md      # API reference (full documentation)
├── RAWLSIAN_FRAMEWORK.md     # Framework philosophy & principles
├── INTERPRETING_RESULTS.md   # How to analyze negotiation results
├── IMPLEMENTATION_SUMMARY.md # Technical implementation details
├── QUICK_REFERENCE.md        # Quick navigation guide
├── modules.rst               # Sphinx autodoc module index
├── index.rst                 # Sphinx main index
├── _static/                  # Sphinx static files
├── _templates/               # Sphinx templates
└── api/                      # API reference (generated by autodoc)
```

---

## Environment & Dependency Management

### Python Version
- **Required**: Python 3.14+
- **Managed via**: `.python-version` file (pyenv integration)
- **Current**: 3.14

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
- `dspy>=3.1.3` - AI/ML pipeline framework
- `langchain>=1.2.10` - LLM chains and utilities
- `langchain-openai>=1.1.9` - OpenAI integration
- `langgraph>=1.0.8` - State graph-based agent orchestration
- `openai>=2.20.0` - OpenAI API client
- `ollama>=0.6.1` - Local LLM support (Ollama)
- `ragas>=0.4.3` - RAG assessment framework
- `psycopg>=3.3.2` - PostgreSQL client (for future DB integration)
- `streamlit>=1.54.0` - Web UI framework (optional)
- `sphinx-rtd-theme>=3.1.0` - Documentation theme

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
| `CHAT_MODEL` | `gpt-4o-mini` | Cloud LLM model (OpenAI) |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Cloud embedding model |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434/v1` | Local LLM API endpoint |
| `LOCAL_LLM_MODEL` | `glm-4.7-flash` | Local chat model name |
| `LOCAL_EMBEDDING_MODEL` | `nomic-embed-text` | Local embedding model |
| `LOCAL_LLM_API_KEY` | (empty) | Local LLM API key (optional) |

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

**Example 1: Rental Negotiation (3 parties)**
```bash
cd <repository-root>
python examples/negotiate_claim.py
```
Runs: `example_contract_negotiation()`, `example_async_negotiation()`, `example_simple_negotiation()`

**Example 2: Claims Extraction**
```bash
python examples/extract_claims.py
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

### negotiation_swarm.py (450 lines) - Primary Module

**Key Class**: `NegotiationSwarm`
- **Purpose**: Orchestrate multi-agent negotiation via LangGraph
- **Constructor**: `__init__(roles, impartial_spectator, initial_claim, model=None, temperature=0.7, max_rounds=50)`
- **Main Methods**:
  - `negotiate()` - Synchronous execution
  - `negotiate_async()` - Asynchronous execution
- **Internal Methods**:
  - `_build_graph()` - Creates LangGraph state machine
  - `_create_role_node(role)` - Creates evaluation node for a role
  - `_create_spectator_node()` - Creates fairness validation node
  - `_route_after_role()` - Routes to next agent or ends
  - `_random_next_role()` - Selects next role randomly (prioritizing unsatisfied)

**Key State Type**: `NegotiationState`
- `current_claim: str` - Current terms being negotiated
- `proposed_claim: str | None` - Proposed modification
- `messages: list[BaseMessage]` - Negotiation history
- `satisfied_roles: dict[str, bool]` - Satisfaction status per role
- `proposal_history: list[str]` - Last 5 proposals (prevents cycling)
- `round_count: int` - Iteration counter

**Rawlsian Framework Implementation**:
- Uses role prompt evaluating claims for **conscionability**, **power imbalances**, **vulnerability exploitation**, **long-term risks**
- Agents respond with `SATISFIED: [reason]` or `PROPOSE: [modification]`
- Impartial spectator validates proposals via "veil of ignorance" test
- Terminates when all satisfied OR max_rounds hit

### config.py (112 lines) - Configuration Management

**Key Functions**:
- `should_use_local_llm()` - Checks env var or CLI flag
- `get_api_key()` - Returns API key (cloud or local)
- `get_base_url()` - Returns LLM endpoint URL
- `get_model()` - Returns model name
- `get_logger(name)` - Returns configured logger

**Usage Pattern**:
```python
from rawlsianagents.config import get_api_key, get_base_url, get_model

api_key = get_api_key()         # Auto-detects cloud vs local
base_url = get_base_url()       # Auto-detects cloud vs local
model = get_model()             # Auto-detects cloud vs local
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

### LangGraph Integration
- **State Machine**: Graph-based agent orchestration (not ReAct or similar)
- **Nodes**: One node per role + spectator node + finalize node
- **Edges**: Conditional routing based on satisfaction and max_rounds
- **Type Hints**: Uses TypedDict for state (compatible with LangGraph)

### Rawlsian Framework
- **Veil of Ignorance**: "Would you accept if roles were reversed?"
- **Conscionability Test**: Evaluates fairness of terms
- **Vulnerability Assessment**: Identifies exploitation of weak positions
- **Power Balance Check**: Flags asymmetrical leverage
- **Long-term Risk Analysis**: Considers contingencies and external factors

### Response Parsing
Agents respond with explicit format:
- `SATISFIED: [explanation]` - Party is satisfied with current claim
- `PROPOSE: [modification]` - Party proposes specific change

### Proposal History
- Maintains last 5 proposals
- Prevents infinite cycling through identical proposals
- Shown to agents in system prompt to encourage progress

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
│   ├── __init__.py              (exports: NegotiationSwarm, NegotiationState)
│   ├── config.py                (LLM config: local vs cloud)
│   ├── negotiation_swarm.py     (PRIMARY - multi-agent negotiation)
│   ├── claims_extractor.py      (claim parsing & classification)
│   └── utils/                   (reserved for utilities)
│
├── examples/
│   ├── negotiate_claim.py       (3 working examples using NegotiationSwarm)
│   └── extract_claims.py        (example: claim extraction)
│
├── docs/
│   ├── negotiation_swarm.md     (API reference - comprehensive)
│   ├── RAWLSIAN_FRAMEWORK.md    (framework philosophy)
│   ├── QUICK_REFERENCE.md       (quick guide)
│   ├── INTERPRETING_RESULTS.md  (result analysis)
│   ├── IMPLEMENTATION_SUMMARY.md (technical details)
│   ├── conf.py                  (Sphinx config)
│   └── Makefile                 (doc building)
│
├── .env.template                (environment variable template)
├── .env                         (local config - do not commit)
├── .python-version              (Python 3.14)
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

**Document Version**: 1.0  
**Last Updated**: February 17, 2026  
**For**: RawlsianAgents v0.1.0  
**Python**: 3.14+  
**Status**: Production Ready ✓
