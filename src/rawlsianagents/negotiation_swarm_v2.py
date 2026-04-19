"""Negotiation Swarm V2.

This module implements a phase-based democratic negotiation protocol
to achieve [or preserve] fair outputs [inputs] from a given claim:

1. Roles submit private concerns about a claim in random order.
2. An impartial-spectator provides perspective to compare concerns,
   merge overlaps, surface neglected distributive considerations, and propose a
   candidate claim.
3. Roles vote on the spectator proposal, and anonymously provide feedback.

Only the spectator can author candidate claim text during a round. A proposal is
accepted only by unanimous role approval.
"""

import json
import random
from typing import Any, Literal, TypedDict

import dspy

from .config import get_api_key, get_base_url, get_dspy_model, get_logger

logger = get_logger(__name__)

api_key = get_api_key()
base_url = get_base_url()
dspy_model = get_dspy_model()

v2_llm = dspy.LM(
    model=dspy_model,
    api_base=base_url,
    api_key=api_key,
)
dspy.configure(lm=v2_llm)


class NegotiationRound(TypedDict, total=False):
    """Audit record for one round.

    All keys are optional (``total=False``) because the record is built
    incrementally during a round.

    :ivar round: round index.
    :ivar base_claim: Claim text at the start of the round.
    :ivar candidate_claim: Spectator-authored proposal evaluated in the round.
    :ivar concern_packet: Public packet used as the shared voting context.
    :ivar votes: Anonymized vote records for this round.
    :ivar unresolved_concern_ids: Concern IDs left unresolved by rejected votes.
    :ivar accepted: ``True`` if all votes were ACCEPT.
    """

    round: int
    base_claim: str
    candidate_claim: str
    concern_packet: "ConcernPacket"
    votes: list["VoteRecord"]
    unresolved_concern_ids: list[str]
    accepted: bool


class ConcernItem(TypedDict):
    """One public concern produced by the spectator after merging.

    :ivar concern_id: Round-local identifier assigned sequentially (C1, C2, ...).
    :ivar summary: Neutral public summary suitable for voting and justification.
    """

    concern_id: str
    summary: str


class ConcernPacket(TypedDict):
    """Public packet shared with all roles during the voting phase.

    :ivar round: round index.
    :ivar base_claim: Claim text at the start of the round.
    :ivar candidate_claim: Spectator-authored claim proposed for voting.
    :ivar merged_concerns: Anonymized public concern list with stable IDs.
    :ivar spectator_justification: Rationale linking concerns to the candidate claim.
    :ivar spectator_pov: Spectator guidance carried into the next round.
    """

    round: int
    base_claim: str
    candidate_claim: str
    merged_concerns: list[ConcernItem]
    spectator_justification: str
    spectator_pov: str


VoteDecision = Literal["ACCEPT", "REJECT"]


class VoteRecord(TypedDict):
    """Anonymized vote result for one role in one round.

    :ivar vote_id: Anonymous sequential identifier (V1, V2, ...).
    :ivar vote: Decision cast by the role.
    :ivar rationale: Public justification for the vote decision.
    :ivar unmet_concern_ids: Concern IDs from the current packet the voter considers unresolved.
        Scoped to the current round; new concerns emerge in next round via synthesis.
    """

    vote_id: str
    vote: VoteDecision
    rationale: str
    unmet_concern_ids: list[str]


class RoleConcern(dspy.Signature): ###You need to review this class, methods and interactions, last_accepted_claim makes no sense.
    """Collect one private role concern and one recommendation.

    Invoked once per role per round before spectator synthesis via
    ``dspy.ChainOfThought(RoleConcern)``.

    :param role: Role label used only for private, role-local reasoning.
    :param current_claim: Claim text currently under negotiation.
    :param spectator_pov: Spectator perspective carried from the prior round.
    :returns concern: Role's primary objection or fairness concern.
    :returns recommendation: Concrete adjustment the role proposes.
    """

    role: str = dspy.InputField(desc="Role label for private role-local reasoning")
    current_claim: str = dspy.InputField(desc="Claim text currently under negotiation")
    spectator_pov: str = dspy.InputField(
        desc="Prior spectator perspective to widen role reasoning"
    )

    concern: str = dspy.OutputField(desc="Primary role concern about the current claim")
    recommendation: str = dspy.OutputField(
        desc="Concrete role recommendation addressing the concern"
    )


class SpectatorSynthesis(dspy.Signature):
    """Impartial spectator synthesis in the spirit of Adam Smith and Amartya Sen.

    Merges anonymized private role submissions into a public concern list,
    authors one candidate claim that addresses all concerns, if possible, and emits a
    spectator perspective to improve next-round role reasoning, for example, if
    the concerns were due to missing information or faulty reasoning.

    Constraints enforced by the spectator:

    - **Anonymity**: no role names, submission order, or identifying quotes.
    - **Merging**: overlapping concerns must be collapsed into one concern ID.
    - **Coverage**: every distinct concern must appear in ``merged_concerns``.
    - **No-envy lens**: asymmetry alone is not injustice; evaluate full bundles of benefits and responsibilities.
    - **Permutation robustness**: conclusions must not change when role labels or
      submission order are permuted.
    - ``merged_concerns`` entries must include ``concern_id`` (C1, C2, ...)
      and ``summary`` (neutral public text).
    - ``justification`` and ``spectator_pov`` must reference concern IDs only.

    :param current_claim: Claim text currently under evaluation.
    :param private_submissions: Anonymized concern/recommendation pairs from roles.
    :param rejection_feedback: Public feedback from previously rejected candidates.
    :returns merged_concerns: Public concern entries with concern_id and summary.
    :returns candidate_claim: Complete spectator-authored claim proposed for voting.
    :returns justification: Public rationale referencing concern IDs and tradeoffs.
    :returns spectator_pov: Perspective to inform and improve next-round reasoning.
    """

    current_claim: str = dspy.InputField(desc="Claim text currently being evaluated")
    private_submissions: list[dict[str, Any]] = dspy.InputField(
        desc="Anonymized concern/recommendation submissions from roles"
    )
    rejection_feedback: str = dspy.InputField(
        desc="Public feedback from previously rejected candidate claims"
    )

    merged_concerns: list[dict[str, Any]] = dspy.OutputField(
        desc="Public concern entries with concern_id and summary"
    )
    candidate_claim: str = dspy.OutputField(
        desc="Complete spectator-authored claim proposed for voting"
    )
    justification: str = dspy.OutputField(
        desc="Public rationale that references concern IDs and tradeoffs"
    )
    spectator_pov: str = dspy.OutputField(
        desc="Perspective to inform and improve next-round role reasoning"
    )


class RoleVote(dspy.Signature):
    """Role voting step over the spectator candidate claim.

    Each role casts an ACCEPT or REJECT vote against the public concern packet.
    Rejection must cite unmet concern IDs from the packet.

    :param role: Role label used only for private voting context.
    :param candidate_claim: Spectator-authored claim proposed this round.
    :param concern_packet: Public packet with merged concerns and justification.
    :returns vote: Structured decision constrained to ACCEPT or REJECT.
    :returns rationale: Publicly shareable reason for the decision.
    :returns unmet_concern_ids: Concern IDs the voter considers still unresolved.
    """

    role: str = dspy.InputField(desc="Role label for private voting context")
    candidate_claim: str = dspy.InputField(desc="Spectator-authored candidate claim text")
    concern_packet: dict[str, Any] = dspy.InputField(
        desc="Public packet containing merged concerns and spectator rationale"
    )

    vote: VoteDecision = dspy.OutputField(desc="Vote decision constrained to ACCEPT or REJECT")
    rationale: str = dspy.OutputField(desc="Publicly shareable reason for vote decision")
    unmet_concern_ids: list[str] = dspy.OutputField(
        desc="Concern IDs from the packet that remain unresolved"
    )





class NegotiationSwarmV2:
    """V2 democratic negotiation engine.

    Runs the three-phase loop—private concern collection, spectator synthesis,
    role voting—until all roles accept a claim or ``max_rounds``
    is reached. Only the spectator authors candidate claim text.

    :ivar roles: Ordered list of participating role labels.
    :ivar initial_claim: Starting claim text before any negotiation rounds.
    :ivar max_rounds: Upper bound on rounds; defaults to 5.
    """

    def __init__(self, roles: list[str], initial_claim: str, max_rounds: int | None = None):
        """Initialize one negotiation session.

        :param roles: Non-empty list of role labels participating in negotiation.
        :param initial_claim: Starting claim text before any deliberation.
        :param max_rounds: Maximum rounds before termination. Defaults to 5 when omitted.
        :raises ValueError: If ``roles`` is empty.
        """
        if not roles:
            raise ValueError("At least one role must be provided")

        self.roles = roles
        self.initial_claim = initial_claim
        self.max_rounds = max_rounds or 5

    def negotiate(self) -> dict[str, Any]:
        """Run the full democratic protocol synchronously.

        :returns: A result dict with keys:

            - ``success`` (bool): whether unanimity was reached.
            - ``rounds`` (list[NegotiationRound]): per-round audit trail.
            - ``iterations`` (int): number of rounds executed.
            - ``final_claim`` (str): accepted claim, or latest if not accepted.
            - ``public_concern_packet`` (ConcernPacket): last published packet.
        :rtype: dict
        """

        current_claim = self.initial_claim
        spectator_pov = ""

        rounds: list[NegotiationRound] = []
        rejection_feedback = ""

        for round_number in range(1, self.max_rounds + 1):
            role_order = random.sample(self.roles, k=len(self.roles))
            private_submissions: list[dict[str, Any]] = []

            concern_chain = dspy.ChainOfThought(RoleConcern)
            for role in role_order:
                response = concern_chain(
                    role=role,
                    current_claim=current_claim,
                    spectator_pov=spectator_pov,
                )
                private_submissions.append(
                    {
                        "concern": response.concern.strip(),
                        "recommendation": response.recommendation.strip(),
                    }
                )

            # Reduce role/order bias for spectator reasoning by removing identity
            # labels and using a canonical ordering unrelated to speaking sequence.
            spectator_submissions = [
                {
                    "submission_id": f"S{idx + 1}",
                    "concern": submission["concern"],
                    "recommendation": submission["recommendation"],
                }
                for idx, submission in enumerate(
                    sorted(
                        private_submissions,
                        key=lambda item: (
                            item.get("concern", "").lower(),
                            item.get("recommendation", "").lower(),
                        ),
                    )
                )
            ]

            synthesis_chain = dspy.ChainOfThought(SpectatorSynthesis)
            synthesis = synthesis_chain(
                current_claim=current_claim,
                private_submissions=spectator_submissions,
                rejection_feedback=rejection_feedback or "None",
                config={"adapter": dspy.JSONAdapter()},
            )

            # Assign sequential concern IDs to the merged concerns from synthesis
            merged_concerns: list[ConcernItem] = [
                {
                    "concern_id": f"C{idx}",
                    "summary": item["summary"],
                }
                for idx, item in enumerate(synthesis.merged_concerns or [], start=1)
                if item.get("summary")
            ]
            candidate_claim = synthesis.candidate_claim or current_claim
            concern_packet: ConcernPacket = {
                "round": round_number,
                "base_claim": current_claim,
                "candidate_claim": candidate_claim,
                "merged_concerns": merged_concerns,
                "spectator_justification": synthesis.justification,
                "spectator_pov": synthesis.spectator_pov,
            }

            vote_chain = dspy.ChainOfThought(RoleVote)
            valid_ids = {item["concern_id"] for item in merged_concerns}
            votes: list[VoteRecord] = []
            unresolved_ids: set[str] = set()
            rejected_votes: list[dict[str, Any]] = []

            for vote_idx, role in enumerate(self.roles, start=1):
                response = vote_chain(
                    role=role,
                    candidate_claim=candidate_claim,
                    concern_packet=concern_packet,
                    config={"adapter": dspy.JSONAdapter()},
                )

                vote_decision: VoteDecision = response.vote
                # Filter and sort unmet IDs to those present in the current packet
                unmet = sorted(
                    {item.upper() for item in response.unmet_concern_ids or []}
                    & valid_ids
                )
                if vote_decision == "REJECT":
                    unresolved_ids.update(unmet)
                    rejected_votes.append(
                        {
                            "unmet_concern_ids": unmet,
                            "rationale": response.rationale,
                        }
                    )

                votes.append(
                    {
                        "vote_id": f"V{vote_idx}",
                        "vote": vote_decision,
                        "rationale": response.rationale,
                        "unmet_concern_ids": unmet,
                    }
                )

            accepted = all(item["vote"] == "ACCEPT" for item in votes)
            round_record: NegotiationRound = {
                "round": round_number,
                "base_claim": current_claim,
                "candidate_claim": candidate_claim,
                "concern_packet": concern_packet,
                "votes": votes,
                "unresolved_concern_ids": sorted(unresolved_ids),
                "accepted": accepted,
            }
            rounds.append(round_record)

            spectator_pov = synthesis.spectator_pov or synthesis.justification or ""
            if accepted:
                current_claim = candidate_claim
                logger.info("V2 consensus reached at round %s", round_number)
                return {
                    "success": True,
                    "rounds": rounds,
                    "iterations": round_number,
                    "final_claim": current_claim,
                    "public_concern_packet": concern_packet,
                }

            # Build structured feedback from rejected votes for next synthesis call
            rejection_feedback = json.dumps(rejected_votes) if rejected_votes else ""

        logger.warning("negotiation reached max rounds without unanimity")
        return {
            "success": False,
            "rounds": rounds,
            "iterations": self.max_rounds,
            "final_claim": current_claim,
            "public_concern_packet": rounds[-1].get("concern_packet", {}) if rounds else {},
        }

    async def negotiate_async(self) -> dict[str, Any]:
        """Async entrypoint delegating to :meth:`negotiate`.

        :returns: Same payload as :meth:`negotiate`.
        :rtype: dict
        """
        return self.negotiate()
