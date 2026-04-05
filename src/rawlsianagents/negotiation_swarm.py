"""
Negotiation Swarm Module

This module implements a multi-agent negotiation system where agents representing
different roles negotiate a claim until all parties are satisfied. Uses LangGraph
to create a swarm pattern with random actor selection.

Information flow
----------------
Roles and the spectator deliberately receive different views of the negotiation
state to prevent tone lock-in (combative or complacent cascades):

- **Role nodes** see only bounded, neutral state:
  - ``current_claim`` — the live claim text on the table
  - ``last_accepted_claim`` — pre-rewrite anchor to limit drift
  - ``spectator_pov`` — the spectator's latest neutral reframing (if any)
  Roles never see the raw history, peer objections, or accumulated notes.

- **Spectator node** sees the full history:
  - ``claims_object`` — complete versioned claim list
  - ``adjustment_notes`` — accumulated role and spectator commentary
  - ``satisfied_roles`` — current per-role satisfaction map
  It distils this into a single ``spectator_pov`` string that roles can read
  next turn, acting as a tone-neutral relay between history and forward reasoning.

- Both roles and the spectator use ``dspy.ChainOfThought`` so that intermediate
  reasoning is explicit and decoupled from the surface pattern of the input.

- Actor selection is uniform-random over all roles + spectator, with the
  constraint that the same actor cannot be chosen twice in a row.
"""

import random
from typing import Any, Mapping, TypedDict

import dspy
from langgraph.graph import END, START, StateGraph

from .config import get_api_key, get_base_url, get_dspy_model, get_logger

logger = get_logger(__name__)

api_key = get_api_key()
base_url = get_base_url()
dspy_model = get_dspy_model()

spectator_llm = dspy.LM(
    model=dspy_model,
    api_base=base_url,
    api_key=api_key,
)
dspy.configure(lm=spectator_llm)


class NegotiationState(TypedDict, total=False):
    """State for the negotiation process.

    Fields:
    - claims_object: Versioned claim history for debugging and convergence checks.
    - adjustment_notes: Full history feed written by all nodes; only the
      spectator reads this as input. Roles receive bounded state instead to
      reduce tone lock-in.
    - spectator_reports: Structured spectator diagnostics for auditability.
    - satisfied_roles: Satisfaction status per role for the current claim.
    - role_last_confirmed_version: Claim version each role last confirmed.
    - agreement_count: Cumulative count of unchanged-claim confirmations.
    - iteration_count: Total number of actor interactions.
    - last_accepted_claim: Pre-rewrite baseline claim text used as an anti-drift
      reference. It is not guaranteed to be unanimously accepted.
    - last_actor: Actor that just completed a turn (used to avoid repeats).
    - spectator_pov: Most recent neutral spectator perspective relayed to roles.
    """

    claims_object: list[dict[str, Any]]
    adjustment_notes: str
    spectator_reports: list[dict[str, Any]]
    satisfied_roles: dict[str, bool]
    role_last_confirmed_version: dict[str, int]
    agreement_count: int
    iteration_count: int
    last_accepted_claim: str
    last_actor: str | None
    spectator_pov: str


# Fairness criterion: envy-freeness (Foley, 1967 — "Resource Allocation and the Public
# Sector", Yale Economic Essays 7(1): 45-98). An allocation is envy-free when no party
# would prefer to exchange their complete position — what they receive and what they must
# do to receive it — with any other party's position.
# https://en.wikipedia.org/wiki/Envy-freeness
class RoleEvaluation(dspy.Signature):
    """Evaluate a claim from a specific role's perspective using the envy-freeness criterion.

    You represent a specific role in this negotiation. First, analyse the claim thoroughly:
    consider both immediate and long-term risks, including financial, emotional, legal, and
    social factors. Assess how external influences, such as economic downturns, job loss,
    family expectations, or legal loopholes, could affect the claim. Specifically evaluate
    whether any vulnerabilities — such as intellectual, economic, situational, emotional stress,
    or relationships of trust — were present and exploited during the claim setup process.
    Identify any power imbalances or concerns about unconscionability.

    Then apply the envy-freeness test to decide whether to revise:

    For every other party named in the claim, ask yourself:
    "Would I prefer to exchange my complete position — everything I will receive and
    everything I must do to receive it — with theirs?"

    If you would NOT prefer to exchange with any other party, the claim is envy-free and
    should be returned unchanged, even if individual terms look asymmetric in isolation.

    If you WOULD prefer to exchange with some other party — meaning their full position
    (what they receive and what they must do to receive it) is a better deal than yours —
    the claim is not envy-free and should be revised so that no rational party would prefer
    another's complete position.

    When revising, aim for an allocation that any party could accept from any position, not
    one that merely improves your share in isolation.

    Inputs:
    - role: Role perspective evaluating the claim.
    - current_claim: Claim text currently on the table.
    - last_accepted_claim: Structural baseline from before the latest rewrite.
    - spectator_pov: Neutral reframing from the impartial spectator, if any.

    Output:
    - revised_claim: If envy-free, return the claim unchanged. If not, return a revised claim
      that no party would prefer to exchange out of.
    - adjustment_note: State which parties you would or would not exchange positions with, and
      why. If you revised the claim, state what principle of fairness guided the revision.
    """

    role: str = dspy.InputField()
    current_claim: str = dspy.InputField()
    last_accepted_claim: str = dspy.InputField()
    spectator_pov: str = dspy.InputField()
    revised_claim: str = dspy.OutputField()
    adjustment_note: str = dspy.OutputField()


class SpectatorAnalysis(dspy.Signature):
    """Analyze negotiation progress and suggest neutral perspectives.

    Review the full versioned claim history, adjustment notes from all agents, and
    current satisfaction statuses. Use the history to identify loops, recurring
    claim patterns, gridlocks, and misaligned parties. Suggest alternative
    perspectives that might help parties find common ground. The output must be
    neutral and limited to impartial analysis.

    Inputs:
    - claims_object: Full versioned claim history from version 0 to latest.
    - adjustment_notes: Aggregated notes produced by roles and spectator so far.
    - satisfied_roles: Per-role satisfaction map for the latest claim version.

    Outputs:
    - loop_status: "No loop detected" or concise cycle summary.
    - gridlock_summary: Brief reason parties are stuck.
    - proposed_pov: Impartial perspective that reframes the conflict.
    """

    claims_object: list[dict[str, Any]] = dspy.InputField()
    adjustment_notes: str = dspy.InputField()
    satisfied_roles: dict[str, bool] = dspy.InputField()
    loop_status: str = dspy.OutputField()
    gridlock_summary: str = dspy.OutputField()
    proposed_pov: str = dspy.OutputField()


class NegotiationSwarm:
    """
    A multi-agent negotiation system where agents representing different roles
    negotiate a claim until all parties reach satisfaction.
    
    The system creates a swarm of agents (one per role) that:
    - Review the current claim from their role's perspective
    - Propose modifications or extensions if unsatisfied
    - Hand off to another randomly selected actor (role or spectator)
    - Allow impartial spectator intervention at any point for equilibrium context
    - Terminate when all agents are satisfied or max iterations reached
    
    Attributes:
        roles: List of role descriptions for the negotiating agents
        initial_claim: The starting claim to negotiate
    """
    
    def __init__(
        self,
        roles: list[str],
        initial_claim: str,
    ):
        """
        Initialize the negotiation swarm.
        
        Args:
            roles: List of role descriptions (e.g., ["Landlord", "Tenant", "Property Manager"])
            initial_claim: The initial claim to be negotiated
        """
        if not roles:
            raise ValueError("At least one role must be provided")
        
        self.roles = roles
        self.initial_claim = initial_claim
        self.max_iterations = len(roles) * 10
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(
            "Initialized NegotiationSwarm with "
            f"{len(roles)} roles and max iterations {self.max_iterations}"
        )
    
    def _build_graph(self):
        """Build the LangGraph state graph for the negotiation swarm."""
        
        # Create the graph
        workflow = StateGraph(NegotiationState)
        
        # Add a node for each role
        for role in self.roles:
            node_name = self._role_to_node_name(role)
            workflow.add_node(node_name, self._create_role_node(role))
        
        # Add the impartial spectator node
        workflow.add_node("spectator", self._create_spectator_node())
        
        # Add the final output node
        workflow.add_node("finalize", self._finalize_node)
        
        # START dispatches to the next actor or finalize
        workflow.add_conditional_edges(
            START,
            self._route_after_turn
        )
        
        # Add conditional edges from each role to next actor or finalize
        for role in self.roles:
            node_name = self._role_to_node_name(role)
            workflow.add_conditional_edges(
                node_name,
                self._route_after_turn
            )
        
        # From spectator, route to next actor or finalize
        workflow.add_conditional_edges(
            "spectator",
            self._route_after_turn
        )
        
        # Finalize leads to END
        workflow.add_edge("finalize", END)
        
        return workflow.compile()

    def _role_to_node_name(self, role: str) -> str:
        """Convert a role description to a valid node name."""
        # Simple conversion: lowercase and replace spaces with underscores
        return f"role_{role.lower().replace(' ', '_').replace('-', '_')}"
    
    def _create_role_node(self, role: str):
        """Create a node function for a specific role."""

        def role_node(state: NegotiationState) -> dict[str, Any]:
            """Process negotiation from this role's perspective."""

            claims_object = state.get("claims_object", [])
            if not claims_object:
                claims_object = [
                    {"version": 0, "claim": self.initial_claim, "updated_by": "initial"}
                ]

            latest_claim = claims_object[-1].get("claim", "")
            claim_version = int(claims_object[-1].get("version", 0))
            adjustment_notes = state.get("adjustment_notes", "")
            iteration_count = state.get("iteration_count", 0)
            last_accepted_claim = state.get("last_accepted_claim", self.initial_claim)
            spectator_pov = state.get("spectator_pov", "")

            logger.info(f"Interaction {iteration_count}: {role} reviewing claim")

            # Roles receive bounded state only — not the full history.
            # Full history (adjustment_notes, claims_object) is preserved in state
            # for the spectator but is NOT passed here to avoid tone lock-in.
            evaluate = dspy.ChainOfThought(RoleEvaluation)
            response = evaluate(
                role=role,
                current_claim=latest_claim,
                last_accepted_claim=last_accepted_claim,
                spectator_pov=spectator_pov,
            )
            
            revised_claim = response.revised_claim.strip()
            adjustment_note = response.adjustment_note.strip()
            
            # Parse satisfaction status
            claim_changed = revised_claim != latest_claim

            logger.debug(
                "[ROLE:%s] changed=%s | note: %s | revised: %s",
                role, claim_changed, adjustment_note, revised_claim[:200],
            )

            # Append to full history (spectator-only feed).
            new_notes = adjustment_notes
            if new_notes:
                new_notes += "\n\n"
            if claim_changed:
                new_notes += (
                    f"[Claim Updated by {role}] latest_claim changed and "
                    "all role satisfactions were reset.\n"
                )
            new_notes += f"[{role}] {adjustment_note}"

            if claim_changed:
                # Preserve caller's last accepted claim before clobbering.
                new_last_accepted_claim = latest_claim
                satisfied_roles = {role_name: False for role_name in self.roles}
                role_last_confirmed_version = {
                    role_name: -1 for role_name in self.roles
                }
                new_claim_version = claim_version + 1
                updated_claims_object = [
                    *claims_object,
                    {
                        "version": new_claim_version,
                        "claim": revised_claim,
                        "updated_by": role,
                    },
                ]
            else:
                new_last_accepted_claim = last_accepted_claim
                satisfied_roles = state.get("satisfied_roles", {}).copy()
                role_last_confirmed_version = state.get(
                    "role_last_confirmed_version", {}
                ).copy()
                new_claim_version = claim_version
                updated_claims_object = claims_object

            satisfied_roles[role] = True
            role_last_confirmed_version[role] = new_claim_version

            # Increment only when a role confirms the existing claim (no revision).
            agreement_count = state.get("agreement_count", 0) + int(not claim_changed)

            return {
                "claims_object": updated_claims_object,
                "adjustment_notes": new_notes,
                "satisfied_roles": satisfied_roles,
                "role_last_confirmed_version": role_last_confirmed_version,
                "iteration_count": iteration_count + 1,
                "agreement_count": agreement_count,
                "last_accepted_claim": new_last_accepted_claim,
                "last_actor": role,
            }
        
        return role_node
    
    def _create_spectator_node(self):
        """Create the impartial spectator analysis node.

        The spectator analyzes the negotiation state when randomly selected to:
        - Identify gridlocks (recurring conflicts)
        - Find misaligned parties
        - Suggest perspectives that might help create consensus
        
        The spectator does not modify the claim or block negotiation.
        Its suggestions are appended to adjustment_notes.
        """
        
        def spectator_node(state: NegotiationState) -> dict[str, Any]:
            """Analyze negotiation state and suggest perspectives for consensus."""

            claims_object = state.get("claims_object", [])
            if not claims_object:
                claims_object = [
                    {"version": 0, "claim": self.initial_claim, "updated_by": "initial"}
                ]
            adjustment_notes = state.get("adjustment_notes", "")
            spectator_reports = state.get("spectator_reports", []).copy()
            satisfied_roles = state.get("satisfied_roles", {})
            iteration_count = state.get("iteration_count", 0)
            latest_version = int(claims_object[-1]["version"])

            logger.info("Spectator analyzing negotiation state")
            
            analyze = dspy.ChainOfThought(SpectatorAnalysis)
            response = analyze(
                claims_object=claims_object,
                adjustment_notes=adjustment_notes or "None",
                satisfied_roles=satisfied_roles or {},
            )
            parsed_report: dict[str, str] = {
                "LOOP_STATUS": response.loop_status.strip() or "Unknown",
                "GRIDLOCK_SUMMARY": response.gridlock_summary.strip() or "Not provided",
                "PROPOSED_POV": response.proposed_pov.strip() or "Not provided",
            }

            spectator_report_entry: dict[str, Any] = {
                "iteration": iteration_count + 1,
                "claim_version": latest_version,
                **parsed_report,
            }
            spectator_reports.append(spectator_report_entry)

            logger.debug(
                "[SPECTATOR] loop=%s | gridlock=%s | pov: %s",
                parsed_report["LOOP_STATUS"],
                parsed_report["GRIDLOCK_SUMMARY"],
                parsed_report["PROPOSED_POV"][:200],
            )

            logger.info("Spectator analysis complete")
            
            # Append spectator suggestions to adjustment notes
            new_notes = adjustment_notes
            if new_notes:
                new_notes += "\n\n"
            new_notes += (
                f"[Impartial Spectator | claim_version={latest_version}] "
                f"{parsed_report}"
            )
            
            return {
                "adjustment_notes": new_notes,
                "spectator_reports": spectator_reports,
                "iteration_count": iteration_count + 1,
                "last_actor": "spectator",
                "spectator_pov": parsed_report["PROPOSED_POV"],
            }
                        
        return spectator_node
    
    def _finalize_node(self, state: NegotiationState) -> dict[str, Any]:
        """Finalize the negotiation and prepare output."""
        
        iteration_count = state.get("iteration_count", 0)
        
        logger.info(f"Negotiation complete after {iteration_count} interactions")
        
        return {}
    
    def _route_after_turn(self, state: NegotiationState) -> str:
        """Decide where to route after any actor turn."""

        iteration_count = state.get("iteration_count", 0)
        
        # Check if max iterations reached
        if iteration_count >= self.max_iterations:
            logger.warning(
                f"Max iterations ({self.max_iterations}) reached, finalizing"
            )
            return "finalize"
        
        # Check if all roles are satisfied on the same unchanged claim version
        if self._has_consensus_on_current_claim(state):
            logger.info("Consensus reached on current claim, finalizing")
            return "finalize"
        
        # Continue rolling random negotiation
        return self._random_next_actor(state)

    def _has_consensus_on_current_claim(self, state: Mapping[str, Any]) -> bool:
        """Return True when all roles confirm satisfaction on current claim version."""

        claims_object = state.get("claims_object", [])
        if not claims_object:
            return False

        claim_version = int(claims_object[-1]["version"])
        satisfied_roles = state.get("satisfied_roles", {})
        role_last_confirmed_version = state.get("role_last_confirmed_version", {})

        return all(
            satisfied_roles.get(role, False)
            and role_last_confirmed_version.get(role, -1) == claim_version
            for role in self.roles
        )
    
    def _random_next_actor(self, state: NegotiationState) -> str:
        """Select the next actor randomly, excluding the actor that just acted."""

        last_actor = state.get("last_actor")
        candidates = [
            r for r in self.roles + ["spectator"] if r != last_actor
        ]
        actor = random.choice(candidates)
        if actor == "spectator":
            return "spectator"
        return self._role_to_node_name(actor)
    
    def negotiate(self) -> dict:
        """
        Run the negotiation process.
        
        Returns:
            dict containing:
                - claims_object: Versioned claim history for debugging
                - adjustment_notes: Version control notes from agents and spectator
                - spectator_reports: Structured spectator diagnostics
                - iterations: Number of negotiation interactions
                - agreement_count: Cumulative unchanged-claim confirmations
                - success: Whether all parties reached satisfaction
                - satisfied_roles: Final satisfaction status per role
        """
        
        logger.info("Starting negotiation")
        
        # Initialize state
        initial_state: NegotiationState = {
            "claims_object": [
                {"version": 0, "claim": self.initial_claim, "updated_by": "initial"}
            ],
            "adjustment_notes": "",
            "spectator_reports": [],
            "satisfied_roles": {role: False for role in self.roles},
            "role_last_confirmed_version": {role: -1 for role in self.roles},
            "agreement_count": 0,
            "iteration_count": 0,
            "last_accepted_claim": self.initial_claim,
            "last_actor": None,
            "spectator_pov": "",
        }

        final_state = self.graph.invoke(initial_state)  # type: ignore
        
        success = self._has_consensus_on_current_claim(final_state)
        final_claims_object = final_state.get("claims_object", initial_state["claims_object"])
        
        return {
            "claims_object": final_claims_object,
            "adjustment_notes": final_state.get("adjustment_notes", ""),
            "spectator_reports": final_state.get("spectator_reports", []),
            "iterations": final_state.get("iteration_count", 0),
            "agreement_count": final_state.get("agreement_count", 0),
            "success": success,
            "satisfied_roles": final_state.get("satisfied_roles", {}),
        }
    
    async def negotiate_async(self) -> dict:
        """
        Run the negotiation process asynchronously.
        
        Returns:
            dict containing:
                - claims_object: Versioned claim history for debugging
                - adjustment_notes: Version control notes from agents and spectator
                - spectator_reports: Structured spectator diagnostics
                - iterations: Number of negotiation interactions
                - agreement_count: Cumulative unchanged-claim confirmations
                - success: Whether all parties reached satisfaction
                - satisfied_roles: Final satisfaction status per role
        """
        
        logger.info("Starting async negotiation")
        
        # Initialize state
        initial_state: NegotiationState = {
            "claims_object": [
                {"version": 0, "claim": self.initial_claim, "updated_by": "initial"}
            ],
            "adjustment_notes": "",
            "spectator_reports": [],
            "satisfied_roles": {role: False for role in self.roles},
            "role_last_confirmed_version": {role: -1 for role in self.roles},
            "agreement_count": 0,
            "iteration_count": 0,
            "last_accepted_claim": self.initial_claim,
            "last_actor": None,
            "spectator_pov": "",
        }

        # Run the graph asynchronously
        final_state = await self.graph.ainvoke(initial_state)  # type: ignore
        
        success = self._has_consensus_on_current_claim(final_state)
        final_claims_object = final_state.get("claims_object", initial_state["claims_object"])
        
        return {
            "claims_object": final_claims_object,
            "adjustment_notes": final_state.get("adjustment_notes", ""),
            "spectator_reports": final_state.get("spectator_reports", []),
            "iterations": final_state.get("iteration_count", 0),
            "agreement_count": final_state.get("agreement_count", 0),
            "success": success,
            "satisfied_roles": final_state.get("satisfied_roles", {}),
        }