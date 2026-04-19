"""Minimal negotiation example with the LeVan claim and roles."""

import json
from datetime import UTC, datetime
from pathlib import Path

from rawlsianagents import NegotiationSwarm
from rawlsianagents.utils import compute_claim_semantic_distance


def _print_round_diagnostics(rounds: list[dict]) -> None:
    """Print round-by-round diagnostics for vote outcomes and rationale."""
    if not rounds:
        print("\nNo rounds were recorded.")
        return

    print("\nRound diagnostics:")
    for round_data in rounds:
        round_number = round_data.get("round")
        accepted = round_data.get("accepted")
        spectator_commentary = round_data.get("spectator_commentary", "")
        votes = round_data.get("votes", [])

        print("\n" + "=" * 72)
        print(f"Round {round_number} | accepted={accepted}")
        print("Base claim:")
        print(round_data.get("base_claim", ""))
        print("Candidate claim:")
        print(round_data.get("candidate_claim", ""))

        print("Spectator commentary:")
        print(spectator_commentary)

        print("Votes:")
        if not votes:
            print("  - None")
        for vote in votes:
            print(f"  - {vote.get('vote_id', 'N/A')} -> {vote.get('vote', 'N/A')}")
            print(f"    rationale: {vote.get('rationale', '')}")


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
    initial_claim = claim
    final_claim = result["final_claim"]

    semantic_distance = compute_claim_semantic_distance(
        initial_claim=initial_claim,
        final_claim=final_claim,
    )
    rounds = result.get("rounds", [])
    latest_round = rounds[-1] if rounds else {}
    votes = latest_round.get("votes", [])
    accept_count = sum(1 for vote in votes if vote.get("vote") == "ACCEPT")
    total_votes = len(votes)

    stats_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "roles": roles,
        "success": result["success"],
        "rounds_count": result["rounds_count"],
        "initial_claim": initial_claim,
        "final_claim": final_claim,
        "semantic_distance": semantic_distance.to_dict(),
        "accept_votes_count": accept_count,
        "reject_votes_count": total_votes - accept_count,
        "accept_rate": accept_count / total_votes if total_votes else 0.0,
        "spectator_commentary": result.get("spectator_commentary", ""),
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
    print("\nLatest vote summary:")
    print(
        {
            "accept_votes": accept_count,
            "reject_votes": total_votes - accept_count,
            "total_votes": total_votes,
        }
    )
    _print_round_diagnostics(rounds)
    print("\nStats JSON written to:")
    print(output_file)


if __name__ == "__main__":
    main()
