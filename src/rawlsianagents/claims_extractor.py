from typing import Literal

import dspy
from openai import OpenAI
from ragas.llms import llm_factory
from ragas.metrics._factual_correctness import FactualCorrectness
from tqdm.asyncio import tqdm

from .config import (get_api_key, get_base_url, get_dspy_model, get_logger,
                     get_model, should_use_local_llm)

logger = get_logger(__name__)

# Initialize LLM configuration
api_key = get_api_key()
base_url = get_base_url()
model = get_model()
dspy_model = get_dspy_model()

llm_type = "local" if should_use_local_llm() else "cloud"
logger.info(f"Using {llm_type} LLM with base URL: {base_url} and model: {model}")

ragas_client = OpenAI(api_key=api_key, base_url=base_url)

claims_extractor_llm = llm_factory(
    model=model,
    provider="openai",
    client=ragas_client,
)

# Use High Atomicity and High Coverage for detailed and comprehensive breakdown
claims_extractor = FactualCorrectness(
    llm=claims_extractor_llm,  # type: ignore
    atomicity="high",
    coverage="high",
)

claims_classifier_llm = dspy.LM(
    model=dspy_model,
    api_base=base_url,
    api_key=api_key,
)
dspy.configure(lm=claims_classifier_llm)

class Claims:
    """Wrapper for claims that enables chained operations like classify_claims()."""

    def __init__(self, claims: list[str]):
        self.claims = claims

    async def classify_claims(self) -> list[tuple[str, Literal["factual", "negotiable"]]]:
        """
        Classify all claims as either 'factual' or 'negotiable'. 'factual' claims are
        statements in the contract that are standard or purely descriptive 
        (e.g. definitions, standard legal language, administrative procedures, signature spaces).
        'negotiable' claims are those that affect any of the parties (e.g. payment terms, 
        delivery dates, liability limits, performance obligations, pricing, rights and restrictions).

        Returns:
            List of tuples containing (claim, classification)
        """
        classification_tasks = [self._classify_claim(claim) for claim in self.claims]
        classifications = await tqdm.gather(
            *classification_tasks, desc="Classifying claims"
        )

        return list(zip(self.claims, classifications))

    async def _classify_claim(self, claim: str) -> Literal["factual", "negotiable"]:
        """
        Classify a claim as either 'factual' (standard/descriptive claims) or 'negotiable' 
        (affects parties).

        Args:
            claim: The claim text to classify

        Returns:
            "factual" if the claim is a standard or descriptive clause in a contract,
            "negotiable" if the claim affects any of the parties involved
        """
        classify_task = dspy.ChainOfThought("claim -> classification")
        
        response = classify_task(claim=claim)

        classification = response.classification
        
        if classification not in ["factual", "negotiable"]:
            logger.warning(
                f"Unexpected classification response: {classification}, "
                f"defaulting to 'negotiable'"
            )
            classification = "negotiable"

        return classification  # type: ignore


async def decompose_claims(text: str, callbacks=None) -> Claims:
    """
    Extract claims from text and return a Claims object that enables chained operations.

    Args:
        text: The text to extract claims from
        callbacks: Optional callbacks for the underlying extractor

    Returns:
        Claims object with extracted claims
    """
    extracted = await claims_extractor.decompose_claims(text, callbacks=callbacks)
    return Claims(extracted)