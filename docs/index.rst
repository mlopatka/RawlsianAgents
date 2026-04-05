RawlsianAgents Documentation
=============================

RawlsianAgents is an implementation of LLM-based contract negotiation and fairness assessment, using multi-agent simulated debate to analyze, negotiate, and redraft contracts through claim extraction and classification.

**Features:**

- **Claim Extraction & Classification** – Parse contracts and classify claims as factual (descriptive) or negotiable (affecting any of the parties)
- **Negotiation Simulation** – Multi-agent debate with bounded role inputs and spectator-mediated history relay
- **Contract Drafting** – Synthesize factual claims + revised negotiable claims into final contracts
- **Fairness Assessment** – Compute dispute scores and semantic similarity metrics to gauge initial injustice/ambiguity
- Support for both cloud (OpenAI) and local (Ollama) LLMs

Quick Start
-----------

Extract and classify claims from a document:

.. code-block:: python

    from rawlsianagents.claims_extractor import decompose_claims

    # Extract and classify claims
    claims_obj = decompose_claims(contract_text)
    classified_claims = await claims_obj.classify_claims()
    
    # Results are tuples of (claim, classification)
    for claim, classification in classified_claims:
        print(f"[{classification}] {claim}")

API Documentation
------------------

.. toctree::
   :maxdepth: 2

   modules

Configuration
-------------

Set environment variables to configure the LLM:

- ``USE_LOCAL_LLM``: Set to ``1`` to use local LLM (default: uses OpenAI)
- ``LOCAL_LLM_BASE_URL``: Base URL for local LLM (default: ``http://localhost:11434/v1``)
- ``LOCAL_LLM_MODEL``: Model name for local LLM (default: ``glm-4.7-flash``)
- ``OPENAI_API_KEY``: API key for OpenAI (required if not using local LLM)
- ``CHAT_MODEL``: Chat model to use (default: ``Qwen/Qwen3-235B-A22B``)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
