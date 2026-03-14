"""Distribution analysis of negotiation outcomes across four experimental tiers.

Tier 1 — Unfair marriage contract (LeVan case):
    The initial claim is objectively unfair. We run 30 independent negotiations
    and measure how much the swarm corrects it.

Tier 2 — Re-negotiation of Tier-1 outputs (sanity check):
    Each already-negotiated Tier-1 output is passed through the swarm once more.
    Expected: less semantic change and fewer iterations, confirming the swarm
    does not add noise to claims it has already balanced.

Tier 3 — Taxi fare split from an already-fair Shapley clause (stability check):
    The initial claim already encodes the Shapley-consistent split
    ($3.33 / $8.33 / $18.34). This tier tests whether the engine avoids
    unnecessary meddling when a clause is already fair.

Tier 4 — Taxi fare split from unfair equal split (non-trivial recovery):
    Three passengers share a $30 taxi for 10, 20, and 30 miles respectively.
    The initial claim splits the fare equally ($10 each), which is objectively
    unfair by the Shapley principle (fair split: $3.33 / $8.33 / $18.34).
    This tier tests whether the swarm converges toward Shapley-consistent
    reasoning from first principles, without knowing the formula.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from rawlsianagents import NegotiationSwarm
from rawlsianagents.utils import compute_claim_semantic_distance

logging.basicConfig(level=logging.WARNING)

N_RUNS = 30
BATCH_SIZE = 5

MARRIAGE_ROLES = ["LeVan family", "bride", "groom", "potential children"]
MARRIAGE_UNFAIR_CLAIM = (
    "The marriage contract excludes all of the husband's business interests "
    "from net family property and limits the wife's right to support."
)

TAXI_ROLES = [
    "Passenger A (travels 10 miles)",
    "Passenger B (travels 20 miles)",
    "Passenger C (travels 30 miles)",
]
TAXI_UNFAIR_CLAIM = (
    "Passengers A, B, and C shall each pay $10.00 for the shared $30 taxi fare, "
    "regardless of the distance each passenger travels."
)
TAXI_SHAPLEY_FAIR_CLAIM = (
    "Passengers A, B, and C shall split the $30 taxi fare according to distance "
    "traveled: Passenger A pays $3.33, Passenger B pays $8.33, and Passenger C "
    "pays $18.34."
)


async def _run_one(claim: str, roles: list[str]) -> dict:
    swarm = NegotiationSwarm(roles=roles, initial_claim=claim)
    return await swarm.negotiate_async()


async def _run_batch(
    inputs: list[tuple[str, list[str]]],
    label: str,
) -> list[dict]:
    results: list[dict] = []
    for i in range(0, len(inputs), BATCH_SIZE):
        batch = inputs[i : i + BATCH_SIZE]
        batch_results = await asyncio.gather(*[_run_one(c, r) for c, r in batch])
        results.extend(batch_results)
        done = min(i + BATCH_SIZE, len(inputs))
        print(f"  [{label}] {done}/{len(inputs)} complete")
    return results


def _extract_metrics(initial_claim: str, result: dict) -> dict:
    claims_object = result["claims_object"]
    final_claim = claims_object[-1]["claim"]
    sem = compute_claim_semantic_distance(initial_claim, final_claim)
    n_roles = len(result["satisfied_roles"])
    return {
        "semantic_distance": sem.distance,
        "iterations": result["iterations"],
        "claim_versions": len(claims_object),
        "satisfaction_rate": (
            sum(result["satisfied_roles"].values()) / n_roles if n_roles else 0.0
        ),
        "success": result["success"],
        "final_claim": final_claim,
    }


def _plot_distributions(
    tier1: list[dict],
    tier2: list[dict],
    tier3: list[dict],
    tier4: list[dict],
    output_path: Path,
) -> None:
    metrics = [
        ("semantic_distance", "Semantic Distance\n(initial → final claim)"),
        ("iterations", "Iterations to Convergence"),
        ("claim_versions", "Claim Versions (rewrites)"),
        ("satisfaction_rate", "Satisfaction Rate"),
    ]
    tier_specs = [
        (tier1, "Tier 1 — Unfair marriage claim", "#e07b54"),
        (tier2, "Tier 2 — Re-negotiated outputs (sanity)", "#5b8db8"),
        (tier3, "Tier 3 — Taxi split (already fair Shapley)", "#6abf69"),
        (tier4, "Tier 4 — Taxi split (unfair equal split)", "#af7ac5"),
    ]

    fig, axes = plt.subplots(1, len(metrics), figsize=(18, 5))
    fig.suptitle(
        "Distributional Properties of the Rawlsian Negotiation Engine",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    for ax, (metric, label) in zip(axes, metrics):
        all_values = [
            d[metric] for data, _, _ in tier_specs for d in data
        ]
        for data, tier_label, color in tier_specs:
            values = [d[metric] for d in data]
            # Guard against degenerate distributions (e.g. all-identical values)
            if len(set(values)) > 1:
                sns.kdeplot(
                    values,
                    ax=ax,
                    label=tier_label,
                    color=color,
                    fill=True,
                    alpha=0.25,
                    linewidth=2,
                )
            mean_val = sum(values) / len(values)
            ax.axvline(
                mean_val,
                color=color,
                linestyle="--",
                linewidth=1.4,
                alpha=0.9,
                label=f"{tier_label} mean={mean_val:.2f}",
            )

        ax.set_xlabel(label, fontsize=10)
        ax.set_ylabel("Density", fontsize=9)
        if metric == "semantic_distance":
            min_val = min(all_values)
            max_val = max(all_values)
            left = max(0.0, min_val - 0.02)
            right = min(1.0, max_val + 0.02)
            ax.set_xlim(left, right)
        elif metric == "iterations":
            ax.set_xlim(0, max(all_values) + 1)
        elif metric == "claim_versions":
            ax.set_xlim(0, max(all_values) + 1)
        elif metric == "satisfaction_rate":
            ax.set_xlim(0.0, 1.0)
        ax.legend(fontsize=6.5, loc="upper right")
        sns.despine(ax=ax)

    plt.tight_layout()
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    print(f"Plot saved to: {output_path}")


async def main() -> None:
    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Tier 1: negotiating unfair marriage claim × {N_RUNS}...")
    tier1_results = await _run_batch(
        [(MARRIAGE_UNFAIR_CLAIM, MARRIAGE_ROLES)] * N_RUNS,
        label="Tier 1",
    )
    tier1_metrics = [_extract_metrics(MARRIAGE_UNFAIR_CLAIM, r) for r in tier1_results]

    print(f"Tier 2: re-negotiating Tier-1 outputs × {N_RUNS}...")
    tier2_inputs = [(m["final_claim"], MARRIAGE_ROLES) for m in tier1_metrics]
    tier2_results = await _run_batch(tier2_inputs, label="Tier 2")
    tier2_metrics = [
        _extract_metrics(inp[0], r) for inp, r in zip(tier2_inputs, tier2_results)
    ]

    print(f"Tier 3: re-negotiating already-fair Shapley taxi claim × {N_RUNS}...")
    tier3_results = await _run_batch(
        [(TAXI_SHAPLEY_FAIR_CLAIM, TAXI_ROLES)] * N_RUNS,
        label="Tier 3",
    )
    tier3_metrics = [_extract_metrics(TAXI_SHAPLEY_FAIR_CLAIM, r) for r in tier3_results]

    print(f"Tier 4: negotiating unfair taxi equal-split claim × {N_RUNS}...")
    tier4_results = await _run_batch(
        [(TAXI_UNFAIR_CLAIM, TAXI_ROLES)] * N_RUNS,
        label="Tier 4",
    )
    tier4_metrics = [_extract_metrics(TAXI_UNFAIR_CLAIM, r) for r in tier4_results]

    # Persist raw data
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "n_runs": N_RUNS,
        "tier1_label": "Unfair marriage contract (LeVan case)",
        "tier2_label": "Re-negotiation of Tier-1 outputs (sanity check)",
        "tier3_label": "Taxi fare from fair Shapley clause (stability check)",
        "tier4_label": "Taxi fare from unfair equal split (non-trivial recovery)",
        "tier1": tier1_metrics,
        "tier2": tier2_metrics,
        "tier3": tier3_metrics,
        "tier4": tier4_metrics,
    }
    json_path = output_dir / "distribution_analysis.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Raw data saved to: {json_path}")

    # Generate and save the distribution plot
    plot_path = output_dir / "distribution_analysis.png"
    _plot_distributions(
        tier1_metrics,
        tier2_metrics,
        tier3_metrics,
        tier4_metrics,
        plot_path,
    )


if __name__ == "__main__":
    asyncio.run(main())
