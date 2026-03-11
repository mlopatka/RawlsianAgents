"""Minimal negotiation example with the LeVan claim and roles."""

from rawlsianagents import NegotiationSwarm


def main() -> None:
    roles = ["LeVan family", "bride", "groom", "potential children"]
    claim = (
        "The marriage contract excludes all of the husband's business interests "
        "from net family property and limits the wife's right to support."
    )

    swarm = NegotiationSwarm(
        roles=roles,
        initial_claim=claim,
    )

    result = swarm.negotiate()
    claims_object = result["claims_object"]

    print("Initial claim:")
    print(claims_object[0]["claim"])
    print("Final claim:")
    print(claims_object[-1]["claim"])
    print("\nSatisfied roles:")
    print(result["satisfied_roles"])


if __name__ == "__main__":
    main()
