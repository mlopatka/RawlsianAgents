"""Verbose Tier 3 diagnostic: 3 independent runs of the Shapley-fair taxi claim.

Tier 3 — Shapley-fair taxi claim (stability check):
    Initial claim already encodes the correct Shapley split ($3.33 / $8.33 / $18.34).
    The engine should recognise it as envy-free and return it unchanged.

Output:
    examples/outputs/tier3_verbose.json — full per-run data for analysis.
    Structured log (DEBUG level) printed to stdout / captured via tee.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from rawlsianagents import NegotiationSwarm
from rawlsianagents.utils import compute_claim_semantic_distance

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

TAXI_ROLES = [
    "Passenger A (travels 10 miles)",
    "Passenger B (travels 20 miles)",
    "Passenger C (travels 30 miles)",
]
TAXI_SHAPLEY_FAIR_CLAIM = (
    "Passengers A, B, and C traveled 10, 20, and 30 miles respectively. "
    "They shall split the $30 taxi fare as follows: Passenger A pays $3.33, "
    "Passenger B pays $8.33, and Passenger C pays $18.34."
)
N_RUNS = 3


async def _run_one(run_id: int, claim: str, roles: list[str]) -> dict:
    logging.getLogger(__name__).info("=== RUN %d START ===", run_id)
    swarm = NegotiationSwarm(roles=roles, initial_claim=claim)
    result = await swarm.negotiate_async()
    final_claim = result["final_claim"]
    sem = compute_claim_semantic_distance(claim, final_claim)
    rounds = result.get("rounds", [])
    latest_round = rounds[-1] if rounds else {}
    votes = latest_round.get("votes", [])
    accept_count = sum(1 for vote in votes if vote.get("vote") == "ACCEPT")
    total_votes = len(votes)
    return {
        "run_id": run_id,
        "initial_claim": claim,
        "final_claim": final_claim,
        "semantic_distance": sem.distance,
        "rounds_count": result["rounds_count"],
        "success": result["success"],
        "accept_votes_count": accept_count,
        "reject_votes_count": total_votes - accept_count,
        "spectator_commentary": result.get("spectator_commentary", ""),
        "rounds": rounds,
    }


async def main() -> None:
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    runs = []
    for i in range(1, N_RUNS + 1):
        run = await _run_one(i, TAXI_SHAPLEY_FAIR_CLAIM, TAXI_ROLES)
        runs.append(run)
        print(
            f"\n[RUN {i}] success={run['success']} | "
            f"rounds={run['rounds_count']} | "
            f"semantic_distance={run['semantic_distance']:.4f}"
        )
        print(f"  FINAL: {run['final_claim'][:200]}")

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "criterion": "envy-freeness",
        "n_runs": N_RUNS,
        "tier": "Tier 3 — Taxi fare from Shapley-fair clause (stability check)",
        "runs": runs,
    }
    out = output_dir / "tier3_verbose.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nFull data saved to: {out}")


if __name__ == "__main__":
    asyncio.run(main())
