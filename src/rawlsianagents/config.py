"""
Shared LLM config: cloud (OpenAI) vs local open-source (Ollama).
Set USE_LOCAL_LLM=1 or run Streamlit with --local-llm to use a local model.
"""
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def should_use_local_llm() -> bool:
    """Check if local LLM should be used (env USE_LOCAL_LLM or CLI --local-llm)."""
    env = os.getenv("USE_LOCAL_LLM", "").strip().lower() in ("1", "true", "yes")
    cli = "--local-llm" in sys.argv
    return env or cli


def _get_local_llm_base_url() -> str:
    """Get base URL for local OpenAI-compatible API (e.g. Ollama)."""
    return os.getenv(
        "LOCAL_LLM_BASE_URL",
        "http://localhost:11434/v1",  # Ollama default
    ).rstrip("/")


def _get_local_llm_model() -> str:
    """Get model name for local chat (e.g. llama3.2, mistral, Qwen2-7B-Instruct)."""
    return os.getenv(
        "LOCAL_LLM_MODEL",
        "glm-4.7-flash",  # Ollama default; use any HF model you serve locally
    )


def _get_local_embedding_model() -> str:
    """Get model name for local embeddings (e.g. nomic-embed-text via Ollama)."""
    return os.getenv(
        "LOCAL_EMBEDDING_MODEL",
        "nomic-embed-text",  # Ollama; or match your local embed server
    )


def _get_openai_model() -> str:
    """Get chat model for OpenAI (cloud)."""
    return os.getenv("CHAT_MODEL", "gpt-4o-mini")


def _get_openai_embedding_model() -> str:
    """Get embedding model to use (cloud or local)."""
    return os.getenv("EMBEDDING_MODEL", "intfloat/e5-mistral-7b-instruct")


def _get_openai_base_url() -> str:
    """Get base URL for OpenAI-compatible client."""
    return os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")


def _get_openai_api_key() -> str:
    """API key."""
    return os.getenv("OPENAI_API_KEY", "")


def get_api_key() -> str:
    """Get API key based on LLM modality (local or cloud)."""
    if should_use_local_llm():
        return os.getenv("LOCAL_LLM_API_KEY", "")
    return _get_openai_api_key()


def get_base_url() -> str:
    """Get base URL for LLM based on LLM modality (local or cloud)."""
    if should_use_local_llm():
        return _get_local_llm_base_url()
    return _get_openai_base_url()


def get_model() -> str:
    """Get model name based on LLM modality (local or cloud)."""
    if should_use_local_llm():
        return _get_local_llm_model()
    return _get_openai_model()


def get_embedding_model() -> str:
    """Get embedding model based on LLM modality (local or cloud)."""
    if should_use_local_llm():
        return _get_local_embedding_model()
    return _get_openai_embedding_model()


def get_dspy_model() -> str:
    """Get dspy model string based on LLM modality (local or cloud)."""
    if should_use_local_llm():
        return f"ollama_chat/{_get_local_llm_model()}"
    return f"openai/{_get_openai_model()}"
