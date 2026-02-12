"""
Shared LLM config: cloud (OpenAI) vs local open-source (Ollama).
Set USE_LOCAL_LLM=1 or run Streamlit with --local-llm to use a local model.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def should_use_local_llm() -> bool:
    """Check if local LLM should be used (env USE_LOCAL_LLM or CLI --local-llm)."""
    env = os.getenv("USE_LOCAL_LLM", "").strip().lower() in ("1", "true", "yes")
    cli = "--local-llm" in sys.argv
    return env or cli


def get_local_llm_base_url() -> str:
    """Get base URL for local OpenAI-compatible API (e.g. Ollama)."""
    return os.getenv(
        "LOCAL_LLM_BASE_URL",
        "http://localhost:11434/v1",  # Ollama default
    ).rstrip("/")


def get_local_llm_model() -> str:
    """Get model name for local chat (e.g. llama3.2, mistral, Qwen2-7B-Instruct)."""
    return os.getenv(
        "LOCAL_LLM_MODEL",
        "glm-4.7-flash",  # Ollama default; use any HF model you serve locally
    )


def get_local_embedding_model() -> str:
    """Get model name for local embeddings (e.g. nomic-embed-text via Ollama)."""
    return os.getenv(
        "LOCAL_EMBEDDING_MODEL",
        "nomic-embed-text",  # Ollama; or match your local embed server
    )


def get_chat_model() -> str:
    """Get chat model to use (cloud or local depending on should_use_local_llm())."""
    if should_use_local_llm():
        return get_local_llm_model()
    return os.getenv("CHAT_MODEL", "Qwen/Qwen3-235B-A22B")


def get_embedding_model() -> str:
    """Get embedding model to use (cloud or local)."""
    if should_use_local_llm():
        return get_local_embedding_model()
    return os.getenv("EMBEDDING_MODEL", "intfloat/e5-mistral-7b-instruct")


def get_openai_base_url() -> str:
    """Get base URL for OpenAI-compatible client."""
    if should_use_local_llm():
        return get_local_llm_base_url()
    return os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")


def get_openai_api_key() -> str:
    """API key (empty for many local servers like Ollama)."""
    if should_use_local_llm():
        return os.getenv("LOCAL_LLM_API_KEY", "") or "ollama"  # Ollama ignores key
    return os.getenv("OPENAI_API_KEY", "")
