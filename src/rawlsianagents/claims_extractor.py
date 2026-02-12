from openai import OpenAI
from ragas.llms import llm_factory
from ragas.metrics._factual_correctness import FactualCorrectness
from .config import get_openai_api_key, get_local_llm_base_url, get_local_llm_model

api_key = get_openai_api_key() #defaults to empty string for local servers like Ollama that ignore the key

client = OpenAI(
    api_key=api_key,
    base_url=get_local_llm_base_url()
)

claims_extractor_llm = llm_factory(
    model=get_local_llm_model(),
    provider="openai",
    client=client,
)

# Use High Atomicity and High Coverage when you need a detailed and comprehensive breakdown for in-depth analysis or information extraction.
claims_extractor = FactualCorrectness(
    llm=claims_extractor_llm,
    atomicity="high",
    coverage="high",
)