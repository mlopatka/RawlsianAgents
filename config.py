"""
Shared LLM config: cloud (Nebius/OpenAI) vs local open-source (Ollama, vLLM, Hugging Face).
Set USE_LOCAL_LLM=1 or run Streamlit with --local-llm to use a local model.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def use_local_llm() -> bool:
    """True if local LLM should be used (env USE_LOCAL_LLM or CLI --local-llm)."""
    env = os.getenv("USE_LOCAL_LLM", "").strip().lower() in ("1", "true", "yes")
    cli = "--local-llm" in sys.argv
    return env or cli


def local_llm_base_url() -> str:
    """Base URL for local OpenAI-compatible API (e.g. Ollama, vLLM)."""
    return os.getenv(
        "LOCAL_LLM_BASE_URL",
        "http://localhost:11434/v1",  # Ollama default
    ).rstrip("/")


def local_llm_model() -> str:
    """Model name for local chat (e.g. llama3.2, mistral, Qwen2-7B-Instruct)."""
    return os.getenv(
        "LOCAL_LLM_MODEL",
        "llama3.2",  # Ollama default; use any HF model you serve locally
    )


def local_embedding_model() -> str:
    """Model name for local embeddings (e.g. nomic-embed-text via Ollama)."""
    return os.getenv(
        "LOCAL_EMBEDDING_MODEL",
        "nomic-embed-text",  # Ollama; or match your local embed server
    )


def chat_model() -> str:
    """Chat model to use (cloud or local depending on use_local_llm())."""
    if use_local_llm():
        return local_llm_model()
    return os.getenv("CHAT_MODEL", "Qwen/Qwen3-235B-A22B")


def embedding_model() -> str:
    """Embedding model to use (cloud or local)."""
    if use_local_llm():
        return local_embedding_model()
    return os.getenv("EMBEDDING_MODEL", "intfloat/e5-mistral-7b-instruct")


def openai_base_url() -> str:
    """Base URL for OpenAI-compatible client."""
    if use_local_llm():
        return local_llm_base_url()
    return os.getenv("NEBIUS_API_BASE", "https://api.openai.com/v1")


def openai_api_key() -> str:
    """API key (empty for many local servers like Ollama)."""
    if use_local_llm():
        return os.getenv("LOCAL_LLM_API_KEY", "") or "ollama"  # Ollama ignores key
    return os.getenv("NEBIUS_API_KEY") or os.getenv("OPENAI_API_KEY", "")
