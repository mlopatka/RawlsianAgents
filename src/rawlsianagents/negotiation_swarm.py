"""
Negotiation Swarm Module

This module implements a multi-agent negotiation system where agents representing
different roles negotiate a claim until all parties are satisfied. Uses LangGraph
to create a swarm pattern with random round-robin agent selection.
"""

import random
from typing import Any, TypedDict

import dspy

from langgraph.graph import END, StateGraph

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
        original_claim: The initial claim, never modified.
        latest_claim: The current version of the claim, overwritten by each agent.
        adjustment_notes: Version control notes where agents and spectator append reasoning.
        satisfied_roles: Track satisfaction status (SATISFIED/UNSATISFIED) per role.
        roles_spoken_this_round: Track which roles have spoken in the current round.
        agreement_count: Count of satisfied roles (for statistics).
        round_count: Total number of role interactions (for statistics).
    """

    original_claim: str
    latest_claim: str
    adjustment_notes: str
    satisfied_roles: dict[str, bool]
    roles_spoken_this_round: dict[str, bool]
    agreement_count: int
    round_count: int


class RoleEvaluation(dspy.Signature):
    """Evaluate a claim from a specific role's perspective.
    
    You are an AI representative assigned to analyze and prioritize the interests of the role.
    Your primary responsibility is to identify and evaluate potential future risks that could
    impact the role under the terms of the claim, explicitly assessing whether the claim is
    conscionable.
    
    Consider both immediate and long-term risks, including financial, emotional, legal, and
    social factors. Assess how external influences, such as economic downturns, job loss,
    family expectations, or legal loopholes, could affect the claim. Specifically evaluate
    whether any vulnerabilities—such as intellectual, economic, situational, emotional stress,
    or relationships of trust—were present and exploited during the claim setup process.
    Determine if any power imbalances exist, if the claim disproportionately benefits one
    party, or if it can lead to concerns on unconscionability.
    
    Output:
    - revised_claim: If UNSATISFIED, output the modified claim. If SATISFIED, output the unchanged claim.
    - adjustment_note: Brief explanation of changes made (if unsatisfied) or why satisfied.
    - status: Either 'SATISFIED' or 'UNSATISFIED'
    """

    role: str = dspy.InputField()
    original_claim: str = dspy.InputField()
    latest_claim: str = dspy.InputField()
    adjustment_notes: str = dspy.InputField()
    revised_claim: str = dspy.OutputField()
    adjustment_note: str = dspy.OutputField()
    status: str = dspy.OutputField()


class SpectatorAnalysis(dspy.Signature):
    """Analyze negotiation progress and suggest neutral perspectives.

    Review the original claim, adjustment notes from all agents, and the latest claim version.
    Identify gridlocks, misaligned parties, and suggest alternative perspectives that might
    help parties find common ground. The output must be neutral and must not propose a
    specific resolution.
    """

    original_claim: str = dspy.InputField()
    latest_claim: str = dspy.InputField()
    adjustment_notes: str = dspy.InputField()
    satisfied_roles: dict[str, bool] = dspy.InputField()
    perspective_suggestions: str = dspy.OutputField()


class NegotiationSwarm:
    """
    A multi-agent negotiation system where agents representing different roles
    negotiate a claim until all parties reach satisfaction.
    
    The system creates a swarm of agents (one per role) that:
    - Review the current claim from their role's perspective
    - Propose modifications or extensions if unsatisfied
    - Hand off to another randomly selected agent
    - Track proposal history to avoid discusion loops and detect gridlocks
    - Terminate when all agents are satisfied or max rounds reached
    
    Attributes:
        roles: List of role descriptions for the negotiating agents
        initial_claim: The starting claim to negotiate
    """
    
    def __init__(
        self,
        roles: list[str],
        initial_claim: str,
        max_rounds: int = 20,
    ):
        """
        Initialize the negotiation swarm.
        
        Args:
            roles: List of role descriptions (e.g., ["Landlord", "Tenant", "Property Manager"])
            initial_claim: The initial claim to be negotiated
            max_rounds: Maximum number of negotiation rounds before stopping
        """
        if not roles:
            raise ValueError("At least one role must be provided")
        
        self.roles = roles
        self.initial_claim = initial_claim
        self.max_rounds = max_rounds
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info(f"Initialized NegotiationSwarm with {len(roles)} roles")
    
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
        
        # Add the round reset node
        workflow.add_node("reset_round", self._reset_round_node)
        
        # Add the final output node
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point - start with first role
        workflow.set_entry_point(self._role_to_node_name(self.roles[0]))
        
        # Add conditional edges from each role to next role or spectator for analysis
        for role in self.roles:
            node_name = self._role_to_node_name(role)
            workflow.add_conditional_edges(
                node_name,
                self._route_after_role
            )
        
        # From spectator, go to reset_round to prepare for next round
        workflow.add_edge("spectator", "reset_round")
        
        # From reset_round, route to next role or finalize
        workflow.add_conditional_edges(
            "reset_round",
            self._route_after_reset
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
            
            original_claim = state.get("original_claim", "")
            latest_claim = state.get("latest_claim", "")
            adjustment_notes = state.get("adjustment_notes", "")
            round_count = state.get("round_count", 0)
            
            logger.info(f"Interaction {round_count}: {role} reviewing claim")
            
            # Use DSPy to evaluate the claim from this role's perspective
            evaluate = dspy.Predict(RoleEvaluation)
            response = evaluate(
                role=role,
                original_claim=original_claim,
                latest_claim=latest_claim,
                adjustment_notes=adjustment_notes or "None",
            )
            
            revised_claim = response.revised_claim.strip()
            adjustment_note = response.adjustment_note.strip()
            status_text = response.status.strip().upper()
            
            # Parse satisfaction status
            is_satisfied = "SATISFIED" in status_text
            
            # Append adjustment note to history
            new_notes = adjustment_notes
            if new_notes:
                new_notes += "\n\n"
            new_notes += f"[{role}] {adjustment_note}"
            
            satisfied_roles = state.get("satisfied_roles", {}).copy()
            satisfied_roles[role] = is_satisfied
            roles_spoken_this_round = state.get("roles_spoken_this_round", {}).copy()
            roles_spoken_this_round[role] = True

            # Update state
            updated_state: dict[str, Any] = {
                "latest_claim": revised_claim,
                "adjustment_notes": new_notes,
                "satisfied_roles": satisfied_roles,
                "round_count": round_count + 1,
                "agreement_count": state.get("agreement_count", 0) + (1 if is_satisfied else 0),
                "roles_spoken_this_round": roles_spoken_this_round,
            }
            
            return updated_state
        
        return role_node
    
    def _create_spectator_node(self):
        """Create the impartial spectator analysis node.
        
        The spectator analyzes the negotiation state after each round-robin to:
        - Identify gridlocks (recurring conflicts)
        - Find misaligned parties
        - Suggest perspectives that might help create consensus
        
        The spectator does not modify the claim or block negotiation.
        Its suggestions are appended to adjustment_notes.
        """
        
        def spectator_node(state: NegotiationState) -> dict[str, Any]:
            """Analyze negotiation state and suggest perspectives for consensus."""
            
            original_claim = state.get("original_claim", "")
            latest_claim = state.get("latest_claim", "")
            adjustment_notes = state.get("adjustment_notes", "")
            satisfied_roles = state.get("satisfied_roles", {})

            logger.info("Spectator analyzing negotiation state")
            
            analyze = dspy.Predict(SpectatorAnalysis)
            response = analyze(
                original_claim=original_claim,
                latest_claim=latest_claim,
                adjustment_notes=adjustment_notes or "None",
                satisfied_roles=satisfied_roles or {},
            )
            suggestions = response.perspective_suggestions.strip()
            
            logger.info("Spectator analysis complete")
            
            # Append spectator suggestions to adjustment notes
            new_notes = adjustment_notes
            if new_notes:
                new_notes += "\n\n"
            new_notes += f"[Impartial Spectator] {suggestions}"
            
            return {
                "adjustment_notes": new_notes,
            }
                        
        return spectator_node
    
    def _reset_round_node(self, state: NegotiationState) -> dict[str, Any]:
        """Reset roles_spoken_this_round to start a new round."""
        
        return {
            "roles_spoken_this_round": {role: False for role in self.roles},
        }
    
    def _finalize_node(self, state: NegotiationState) -> dict[str, Any]:
        """Finalize the negotiation and prepare output."""
        
        round_count = state.get("round_count", 0)
        
        logger.info(f"Negotiation complete after {round_count} interactions")
        
        return {}
    
    def _route_after_role(self, state: NegotiationState) -> str:
        """Decide where to route after a role node.
        
        After a role speaks, check if:
        1. All roles have spoken this round (round-robin complete)
        2. If so, go to spectator for analysis
        3. If not, go to next role
        
        Also check if negotiation should end (all satisfied or max rounds).
        """
        
        round_count = state.get("round_count", 0)
        
        # Check if max rounds reached
        if round_count >= self.max_rounds:
            logger.warning(f"Max rounds ({self.max_rounds}) reached, finalizing")
            return "finalize"
        
        # Check if all roles are satisfied
        satisfied_roles = state.get("satisfied_roles", {})
        if all(satisfied_roles.get(role, False) for role in self.roles):
            logger.info("All roles satisfied, finalizing")
            return "finalize"
        
        # Check if all roles have spoken this round
        roles_spoken_this_round = state.get("roles_spoken_this_round", {})
        if all(roles_spoken_this_round.get(role, False) for role in self.roles):
            logger.info("Round-robin complete, sending to spectator for analysis")
            return "spectator"
        
        # Otherwise, continue to another role for this round
        return self._random_next_role(state)
    
    def _route_after_reset(self, state: NegotiationState) -> str:
        """Decide where to route after round reset.
        
        After resetting the round tracker, route to next role or finalize.
        Check if negotiation should end.
        """
        
        round_count = state.get("round_count", 0)
        
        # Check if max rounds reached
        if round_count >= self.max_rounds:
            logger.warning(f"Max rounds ({self.max_rounds}) reached after spectator analysis")
            return "finalize"
        
        # Check if all roles are satisfied
        satisfied_roles = state.get("satisfied_roles", {})
        if all(satisfied_roles.get(role, False) for role in self.roles):
            logger.info("All roles satisfied after spectator analysis, finalizing")
            return "finalize"
        
        # Go to next role to start new round
        return self._random_next_role(state)
    
    def _random_next_role(self, state: NegotiationState) -> str:
        """Select the next role to process randomly from unsatisfied roles."""
        
        satisfied_roles = state.get("satisfied_roles", {})
        
        # Select from unsatisfied roles
        unsatisfied = [role for role in self.roles if not satisfied_roles.get(role, False)]
        selected_role = random.choice(unsatisfied)
        
        return self._role_to_node_name(selected_role)
    
    def negotiate(self) -> dict:
        """
        Run the negotiation process.
        
        Returns:
            dict containing:
                - original_claim: The initial claim
                - final_claim: The negotiated claim
                - adjustment_notes: Version control notes from agents and spectator
                - rounds: Number of negotiation interactions
                - agreement_count: Count of satisfied roles
                - success: Whether all parties reached satisfaction
                - satisfied_roles: Final satisfaction status per role
        """
        
        logger.info("Starting negotiation")
        
        # Initialize state
        initial_state: NegotiationState = {
            "original_claim": self.initial_claim,
            "latest_claim": self.initial_claim,
            "adjustment_notes": "",
            "satisfied_roles": {role: False for role in self.roles},
            "roles_spoken_this_round": {role: False for role in self.roles},
            "agreement_count": 0,
            "round_count": 0,
        }
        
        final_state = self.graph.invoke(initial_state)  # type: ignore
        
        success = all(
            final_state.get("satisfied_roles", {}).get(role, False)
            for role in self.roles
        )
        
        return {
            "original_claim": final_state["original_claim"],
            "final_claim": final_state["latest_claim"],
            "adjustment_notes": final_state.get("adjustment_notes", ""),
            "rounds": final_state.get("round_count", 0),
            "agreement_count": final_state.get("agreement_count", 0),
            "success": success,
            "satisfied_roles": final_state.get("satisfied_roles", {}),
        }
    
    async def negotiate_async(self) -> dict:
        """
        Run the negotiation process asynchronously.
        
        Returns:
            dict containing:
                - original_claim: The initial claim
                - final_claim: The negotiated claim
                - adjustment_notes: Version control notes from agents and spectator
                - rounds: Number of negotiation interactions
                - agreement_count: Count of satisfied roles
                - success: Whether all parties reached satisfaction
                - satisfied_roles: Final satisfaction status per role
        """
        
        logger.info("Starting async negotiation")
        
        # Initialize state
        initial_state: NegotiationState = {
            "original_claim": self.initial_claim,
            "latest_claim": self.initial_claim,
            "adjustment_notes": "",
            "satisfied_roles": {role: False for role in self.roles},
            "roles_spoken_this_round": {role: False for role in self.roles},
            "agreement_count": 0,
            "round_count": 0,
        }
        
        # Run the graph asynchronously
        final_state = await self.graph.ainvoke(initial_state)  # type: ignore
        
        success = all(
            final_state.get("satisfied_roles", {}).get(role, False)
            for role in self.roles
        )
        
        return {
            "original_claim": final_state["original_claim"],
            "final_claim": final_state["latest_claim"],
            "adjustment_notes": final_state.get("adjustment_notes", ""),
            "rounds": final_state.get("round_count", 0),
            "agreement_count": final_state.get("agreement_count", 0),
            "success": success,
            "satisfied_roles": final_state.get("satisfied_roles", {}),
        }