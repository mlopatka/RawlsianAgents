from openai import OpenAI
from ragas.llms import llm_factory
from ragas.metrics._factual_correctness import FactualCorrectness

from .config import (get_local_llm_base_url, get_local_llm_model, get_logger,
                     get_openai_api_key, get_openai_base_url,
                     should_use_local_llm, get_chat_model)

logger = get_logger(__name__)

api_key = get_openai_api_key() #defaults to empty string for local servers like Ollama that ignore the key
local_llm_flag = should_use_local_llm()

if local_llm_flag:
    logger.info(f"Using local LLM with base URL: {get_local_llm_base_url()} and model: {get_local_llm_model()}")
    base_url = get_local_llm_base_url()
    model = get_local_llm_model()
else:
    base_url = get_openai_base_url()
    model = get_chat_model()
    logger.info(f"Using cloud LLM with OpenAI API and model {model}")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

claims_extractor_llm = llm_factory(
    model=model,
    provider="openai",
    client=client,
)

# Use High Atomicity and High Coverage when you need a detailed and comprehensive breakdown for in-depth analysis or information extraction.
claims_extractor = FactualCorrectness(
    llm=claims_extractor_llm, #type: ignore
    atomicity="high",
    coverage="high",
)