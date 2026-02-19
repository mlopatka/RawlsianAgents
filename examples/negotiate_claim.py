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
        max_rounds=20,
    )

    result = swarm.negotiate()

    print("Final claim:")
    print(result["final_claim"])
    print("\nSatisfied roles:")
    print(result["satisfied_roles"])


if __name__ == "__main__":
    main()
