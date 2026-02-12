import asyncio
from rawlsianagents.claims_extractor import claims_extractor


async def main():
    with open("data/LeVan vs LeVan/initial_agreement.md", "r") as f:
        agreement = f.read()

    claims = await claims_extractor.decompose_claims(
        agreement,
        callbacks=None,
    )

    print(claims)


if __name__ == "__main__":
    asyncio.run(main())