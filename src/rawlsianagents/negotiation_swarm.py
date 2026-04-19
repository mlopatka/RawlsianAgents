"""Negotiation Swarm.

A streamlined democratic negotiation loop:

1. Roles evaluate the current working claim and cast ACCEPT/REJECT with rationale.
2. If all accept, the process ends.
3. Otherwise, an impartial spectator reads the vote rationales and proposes a
   revised claim plus one free-text commentary field for outside perspective.
4. The revised claim becomes the next round's working claim.

The initial claim is kept as reference, while the working claim evolves by round.
"""

import random
from typing import Any, Literal, TypedDict

import dspy

from .config import get_api_key, get_base_url, get_dspy_model, get_logger

logger = get_logger(__name__)

api_key = get_api_key()
base_url = get_base_url()
dspy_model = get_dspy_model()

swarm_llm = dspy.LM(
    model=dspy_model,
    api_base=base_url,
    api_key=api_key,
)
dspy.configure(lm=swarm_llm)


VoteDecision = Literal["ACCEPT", "REJECT"]


class VoteRecord(TypedDict):
    """Vote result for one role in one round.

    :ivar vote_id: Anonymous sequential identifier (V1, V2, ...).
    :ivar vote: Decision cast by the role.
    :ivar rationale: Role rationale for ACCEPT or REJECT.
    """

    vote_id: str
    vote: VoteDecision
    rationale: str


class NegotiationRound(TypedDict, total=False):
    """Audit record for one voting round.

    :ivar round: Round index.
    :ivar base_claim: Working claim at round start.
    :ivar votes: Role votes and rationales for the base claim.
    :ivar candidate_claim: Spectator-proposed revision for the next round.
    :ivar spectator_commentary: Single free-text spectator perspective.
    :ivar accepted: ``True`` if all role votes were ACCEPT.
    """

    round: int
    base_claim: str
    votes: list[VoteRecord]
    candidate_claim: str
    spectator_commentary: str
    accepted: bool


class RoleVote(dspy.Signature):
    """Role evaluation and vote over the current claim.

    Evaluate the claim from your role's perspective while accounting for the full
    positions of all parties (benefits and obligations together).

    Decision guidance:

    1. ENVY-FREENESS (complete-position): Would you exchange your entire position
       for another party's entire position?
    2. REASONABLE REJECTABILITY: Could any party reasonably reject this allocation
       from their complete position?

    If acceptable, vote ACCEPT with a concise rationale.
    If not acceptable, vote REJECT with a concise rationale explaining why.

    :param role: Role label for private role-local reasoning.
    :param current_claim: Working claim under evaluation this round.
    :param spectator_commentary: Prior spectator outside perspective.
    :returns vote: Structured decision constrained to ACCEPT or REJECT.
    :returns rationale: Concise role rationale for the decision.
    """

    role: str = dspy.InputField(desc="Role label for role-local reasoning")
    current_claim: str = dspy.InputField(desc="Working claim under evaluation")
    spectator_commentary: str = dspy.InputField(
        desc="Prior spectator outside perspective, if any"
    )

    vote: VoteDecision = dspy.OutputField(desc="Vote decision: ACCEPT or REJECT")
    rationale: str = dspy.OutputField(desc="Role rationale for the vote")


class SpectatorSynthesis(dspy.Signature):
    """Impartial spectator rewrite after role voting.

    You are an impartial spectator in the spirit of Adam Smith and Amartya Sen.
    Read the current claim and role vote rationales, identify missing logic or
    information, and propose a revised claim that better addresses concerns while
    preserving fairness across parties. Use the spectator_commentary field to 
    provide one free-text outside perspective to inform the next round. 
    
    For example, if roles are keen on exposing inequity in distributions, 
    the commentary could highlight the different obligations that support those distributions.

    Output exactly:
    - candidate_claim: revised working claim text for next round.
    - spectator_commentary: one free-text outside perspective to inform next round.

    :param current_claim: Working claim that was just voted on.
    :param vote_feedback: Anonymized vote+rationale list from this round.
    :returns candidate_claim: Revised claim for the next round.
    :returns spectator_commentary: Single free-text outside perspective.
    """

    current_claim: str = dspy.InputField(desc="Working claim that was voted on")
    vote_feedback: list[dict[str, Any]] = dspy.InputField(
        desc="Anonymized role votes and rationales from this round"
    )

    candidate_claim: str = dspy.OutputField(
        desc="Revised claim for the next round"
    )
    spectator_commentary: str = dspy.OutputField(
        desc="One free-text outside perspective"
    )


class NegotiationSwarm:
    """Negotiation engine with a minimal vote-and-rewrite loop.

    :ivar roles: Ordered role labels participating in negotiation.
    :ivar initial_claim: Immutable starting claim for reference.
    :ivar max_vote_rounds: Upper bound on voting rounds.
    """

    def __init__(
        self,
        roles: list[str],
        initial_claim: str,
        max_vote_rounds: int | None = None,
        max_rounds: int | None = None,
    ):
        """Initialize one negotiation session.

        :param roles: Non-empty list of role labels.
        :param initial_claim: Starting claim text.
        :param max_vote_rounds: Maximum voting rounds before termination.
            Defaults to 10 when omitted.
        :param max_rounds: Backward-compatible alias for ``max_vote_rounds``.
        :raises ValueError: If ``roles`` is empty.
        :raises ValueError: If both ``max_vote_rounds`` and ``max_rounds`` are set.
        """
        if not roles:
            raise ValueError("At least one role must be provided")

        if max_vote_rounds is not None and max_rounds is not None:
            raise ValueError("Use either max_vote_rounds or max_rounds, not both")

        effective_max_vote_rounds = (
            max_vote_rounds if max_vote_rounds is not None else max_rounds
        )

        self.roles = roles
        self.initial_claim = initial_claim
        self.max_vote_rounds = effective_max_vote_rounds or 10
        self.max_rounds = self.max_vote_rounds

    def negotiate(self) -> dict[str, Any]:
        """Run synchronous negotiation.

        :returns: Result payload with ``success``, ``rounds``, ``rounds_count``,
            ``final_claim``, and ``spectator_commentary``.
        :rtype: dict
        """
        current_claim = self.initial_claim
        spectator_commentary = ""
        rounds: list[NegotiationRound] = []

        role_vote_chain = dspy.ChainOfThought(RoleVote)
        spectator_chain = dspy.ChainOfThought(SpectatorSynthesis)

        for round_number in range(1, self.max_vote_rounds + 1):
            role_order = random.sample(self.roles, k=len(self.roles))
            votes: list[VoteRecord] = []

            for vote_idx, role in enumerate(role_order, start=1):
                response = role_vote_chain(
                    role=role,
                    current_claim=current_claim,
                    spectator_commentary=spectator_commentary,
                )
                votes.append(
                    {
                        "vote_id": f"V{vote_idx}",
                        "vote": response.vote,
                        "rationale": response.rationale,
                    }
                )

            accepted = all(vote["vote"] == "ACCEPT" for vote in votes)

            if accepted:
                round_record: NegotiationRound = {
                    "round": round_number,
                    "base_claim": current_claim,
                    "votes": votes,
                    "candidate_claim": current_claim,
                    "spectator_commentary": spectator_commentary,
                    "accepted": True,
                }
                rounds.append(round_record)
                logger.info("consensus reached at round %s", round_number)
                return {
                    "success": True,
                    "rounds": rounds,
                    "rounds_count": len(rounds),
                    "final_claim": current_claim,
                    "spectator_commentary": spectator_commentary,
                }

            vote_feedback = [
                {
                    "vote_id": vote["vote_id"],
                    "vote": vote["vote"],
                    "rationale": vote["rationale"],
                }
                for vote in votes
            ]
            synthesis = spectator_chain(
                current_claim=current_claim,
                vote_feedback=vote_feedback,
            )

            candidate_claim = synthesis.candidate_claim or current_claim
            spectator_commentary = synthesis.spectator_commentary or ""

            round_record = {
                "round": round_number,
                "base_claim": current_claim,
                "votes": votes,
                "candidate_claim": candidate_claim,
                "spectator_commentary": spectator_commentary,
                "accepted": False,
            }
            rounds.append(round_record)

            current_claim = candidate_claim

        logger.warning("negotiation reached max vote rounds without unanimity")
        return {
            "success": False,
            "rounds": rounds,
            "rounds_count": len(rounds),
            "final_claim": current_claim,
            "spectator_commentary": spectator_commentary,
        }

    async def negotiate_async(self) -> dict[str, Any]:
        """Async entrypoint delegating to :meth:`negotiate`."""
        return self.negotiate()
