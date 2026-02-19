# NegotiationSwarm Quick Reference

## Getting Started (5 minutes)

### Installation
```bash
cd /home/sergio_ferro/RawlsianAgents
uv sync
```

### First Negotiation
```python
from rawlsianagents import NegotiationSwarm

swarm = NegotiationSwarm(
    roles=["Party A: Description", "Party B: Description"],
    impartial_spectator="Fair evaluator description",
    initial_claim="Initial terms to negotiate"
)

result = swarm.negotiate()
print(result['final_claim'])
```

## Documentation Guide

### For Different Audiences

**Just want to use it?**  
→ See [Quick Start in README.md](../../README.md#quick-start-negotiation-swarm)

**Building your first negotiation?**  
→ See [examples/negotiate_claim.py](../../examples/negotiate_claim.py)

**Want to understand how it works?**  
→ Read [RAWLSIAN_FRAMEWORK.md](RAWLSIAN_FRAMEWORK.md)

**Need complete API reference?**  
→ See [negotiation_swarm.md](negotiation_swarm.md)

**Analyzing negotiation results?**  
→ Check [INTERPRETING_RESULTS.md](INTERPRETING_RESULTS.md)

**Technical implementation details?**  
→ See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

**How negotiation flow is implemented?**  
→ Read [negotiation_swarm.md](negotiation_swarm.md)

## File Locations

| Purpose | Location |
|---------|----------|
| Main Module | `src/rawlsianagents/negotiation_swarm.py` |
| Export | `src/rawlsianagents/__init__.py` |
| Examples | `examples/negotiate_claim.py` |
| API Docs | `docs/negotiation_swarm.md` |
| Framework | `docs/RAWLSIAN_FRAMEWORK.md` |
| Results Analysis | `docs/INTERPRETING_RESULTS.md` |

## Core Concepts

### NegotiationSwarm
Class that orchestrates multi-agent negotiation using LangGraph.

```python
swarm = NegotiationSwarm(
    roles: list[str],                # Parties to negotiate
    impartial_spectator: str,        # Fairness evaluator
    initial_claim: str,              # Starting terms
    model: str = None,               # LLM model
    temperature: float = 0.7,        # LLM temperature
    max_rounds: int = 50             # Negotiation limit
)
```

### NegotiationState
Internal state tracking for the negotiation process.

```python
{
    'current_claim': str,            # Current terms
    'proposed_claim': str | None,    # Proposed modification
    'messages': list[BaseMessage],   # Chat history
    'satisfied_roles': dict,         # Satisfaction status per role
    'proposal_history': list[str],   # Past proposals
    'round_count': int,              # Number of rounds
}
```

### Rawlsian Evaluation
Each role evaluates claims by asking:
- Is this **conscionable** (fundamentally fair)?
- Are there **power imbalances**?
- Are **vulnerabilities** exploited?
- What **long-term risks** exist?

## Common Tasks

### Simple Negotiation (2 parties)
```python
swarm = NegotiationSwarm(
    roles=["Buyer: ...", "Seller: ..."],
    impartial_spectator="Market analyst ensuring fair pricing",
    initial_claim="Price: $500, Terms: ...",
    max_rounds=20
)
result = swarm.negotiate()
```

### Complex Negotiation (3+ parties)
```python
swarm = NegotiationSwarm(
    roles=["Party A", "Party B", "Party C"],
    impartial_spectator="Enhanced fairness description",
    initial_claim="Multi-party terms",
    temperature=0.7,
    max_rounds=40
)
result = swarm.negotiate()
```

### Async Execution
```python
import asyncio

result = await swarm.negotiate_async()
```

### Analyzing Results
```python
print(f"Success: {result['success']}")
print(f"Rounds: {result['rounds']}")
print(f"Final: {result['final_claim']}")

for role, satisfied in result['satisfied_roles'].items():
    print(f"  {role}: {'✓' if satisfied else '✗'}")

# View negotiation history
for msg in result['messages']:
    print(msg.content)
```

## Best Practices

✅ **DO:**
- Include context in role descriptions (concerns, constraints)
- Make initial claims specific and concrete
- Use fairness language in spectator description
- Reference vulnerability types in role prompts
- Set max_rounds based on complexity
- Lower temperature (0.5-0.7) for formal agreements
- Higher temperature (0.7-0.85) for exploratory negotiation

❌ **DON'T:**
- Use vague role names ("Buyer" without context)
- Make initial claims too simple
- Max out max_rounds without increasing temperature
- Use very high temperature (>0.9) for fairness negotiation
- Skip analyzing the messages to understand what happened

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Negotiation doesn't converge | Increase max_rounds, lower temperature, simplify claim |
| Proposals keep repeating | Already handled by proposal_history - check temperature |
| One party never satisfied | Check role description balance, lower temperature |
| Results seem unfair | Strengthen spectator description, review messages |
| LLM errors | Check API key, base_url in config, try local LLM |

## Key Files Reference

### negotiation_swarm.py (Main Implementation)
- `NegotiationSwarm.__init__()` - Initialize
- `NegotiationSwarm.negotiate()` - Run synchronously
- `NegotiationSwarm.negotiate_async()` - Run asynchronously
- `_create_role_node()` - Role evaluation logic
- `_create_spectator_node()` - Fairness validation logic

### Example Usage Patterns
See `examples/negotiate_claim.py` for:
1. `example_contract_negotiation()` - Rental agreement
2. `example_async_negotiation()` - Employment terms (async)
3. `example_simple_negotiation()` - Simple 2-party deal

## Advanced Topics

### Customizing Role Prompt
Subclass `NegotiationSwarm` and override `_create_role_node()`

### Alternative Spectator Logic
Override `_create_spectator_node()` for different fairness frameworks

### Custom Routing
Override `_random_next_role()` for deterministic vs. random selection

### Integration with Pipeline
The module is designed to integrate with:
- `claims_extractor.py` for initial claim parsing
- Fairness metrics from original paper
- Streamlit UI for interactive negotiation

## Performance Guidelines

| Scenario | Rounds | Time | Success |
|----------|--------|------|---------|
| 2 parties, fair initial | 8-15 | ~1-2 min | Very High |
| 2 parties, unfair initial | 20-35 | ~3-5 min | High |
| 3 parties, complex | 30-50 | ~5-10 min | Medium |
| Irreconcilable | 50+ | Timeout | Low |

(Times depend on LLM latency and model choice)

## Getting Help

1. **API Questions**: See [negotiation_swarm.md](negotiation_swarm.md)
2. **Framework Questions**: See [RAWLSIAN_FRAMEWORK.md](RAWLSIAN_FRAMEWORK.md)
3. **Result Interpretation**: See [INTERPRETING_RESULTS.md](INTERPRETING_RESULTS.md)
4. **Implementation Details**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
5. **Flow & State Details**: See [negotiation_swarm.md](negotiation_swarm.md)

## Links

- [Repository](../../)
- [Main README](../../README.md)
- [Full API Documentation](negotiation_swarm.md)
- [Rawlsian Framework Explanation](RAWLSIAN_FRAMEWORK.md)
- [Result Interpretation Guide](INTERPRETING_RESULTS.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Examples](../../examples/negotiate_claim.py)

## Quick Command Reference

```bash
# Run examples
python examples/negotiate_claim.py

# Test import
python -c "from rawlsianagents import NegotiationSwarm; print('OK')"

# Check errors
pyright src/rawlsianagents/negotiation_swarm.py
```

---

**Last Updated**: February 17, 2026  
**Version**: 0.1.0  
**Status**: Production Ready ✓
