import asyncio

from langchain_text_splitters import MarkdownHeaderTextSplitter
from tqdm.asyncio import tqdm

from rawlsianagents.claims_extractor import claims_extractor
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

    # Process all sections concurrently and flatten results
    tasks = [
        claims_extractor.decompose_claims(section.page_content, callbacks=None)
        for section in sections
    ]
    results = await tqdm.gather(*tasks, desc="Processing sections")
    
    # Flatten list of lists into single list, filtering out exceptions
    all_claims = [
        claim 
        for result in results 
        if not isinstance(result, Exception)
        for claim in result #type: ignore
    ]
    
    logger.info(f"Total claims extracted: {len(all_claims)}")
    for i, claim in enumerate(all_claims, 1):
        logger.info(f"{i}. {claim}")


if __name__ == "__main__":
    asyncio.run(main())