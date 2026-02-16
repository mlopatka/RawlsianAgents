import asyncio

from langchain_text_splitters import MarkdownHeaderTextSplitter
from tqdm.asyncio import tqdm

from rawlsianagents.claims_extractor import decompose_and_classify_claims
from rawlsianagents.config import get_logger

logger = get_logger(__name__)

headers_to_split_on = [
    ("#", "H1"),
    ("##", "H2"),
    ("###", "H3"),
    ("####", "H4"),
]


async def main():
    with open("data/LeVan vs LeVan/initial_agreement.md", "r") as f:
        agreement = f.read()
    
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    sections = text_splitter.split_text(agreement)
    
    tasks = [decompose_and_classify_claims(section.page_content) for section in sections]
    classified_results = await tqdm.gather(*tasks, desc="Extracting and classifying claims")
    
    # Flatten results
    all_classified_claims = [
        claim_pair
        for classified_claims in classified_results
        for claim_pair in classified_claims
    ]
    
    logger.info(f"Total claims extracted and classified: {len(all_classified_claims)}")
    
    # Display claims with classifications
    for i, (claim, classification) in enumerate(all_classified_claims, 1):
        logger.info(f"{i}. [{classification.upper()}] {claim}")


if __name__ == "__main__":
    asyncio.run(main())