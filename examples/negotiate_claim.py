"""Minimal negotiation example with the LeVan claim and roles."""

import json
from datetime import UTC, datetime
from pathlib import Path

from rawlsianagents import NegotiationSwarm
from rawlsianagents.utils import compute_claim_semantic_distance


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
    satisfied_roles = result["satisfied_roles"]
    initial_claim = claims_object[0]["claim"]
    final_claim = claims_object[-1]["claim"]

    semantic_distance = compute_claim_semantic_distance(
        initial_claim=initial_claim,
        final_claim=final_claim,
    )
    satisfied_count = sum(1 for is_satisfied in satisfied_roles.values() if is_satisfied)
    total_roles = len(roles)

    stats_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "roles": roles,
        "iterations": result["iterations"],
        "agreement_count": result["agreement_count"],
        "success": result["success"],
        "claim_versions": len(claims_object),
        "spectator_reports_count": len(result["spectator_reports"]),
        "initial_claim": initial_claim,
        "final_claim": final_claim,
        "semantic_distance": semantic_distance.to_dict(),
        "satisfied_roles": satisfied_roles,
        "satisfied_roles_count": satisfied_count,
        "unsatisfied_roles_count": total_roles - satisfied_count,
        "satisfaction_rate": satisfied_count / total_roles if total_roles else 0.0,
    }

    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "negotiation_stats.json"
    output_file.write_text(json.dumps(stats_payload, indent=2), encoding="utf-8")

    print("Initial claim:")
    print(initial_claim)
    print("Final claim:")
    print(final_claim)
    print("Semantic distance:")
    print(semantic_distance.to_dict())
    print("\nSatisfied roles:")
    print(satisfied_roles)
    print("\nStats JSON written to:")
    print(output_file)


if __name__ == "__main__":
    main()
