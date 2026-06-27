"""Escalator Agent - handles human-in-the-loop decisions."""

from src.core.agent_base import BaseAgent
from src.config import settings


class EscalatorAgent(BaseAgent):
    name = "escalator"
    model = settings.model_reasoning  # Needs to reason about what context to present
    description = "Handles human escalation with full context and reasoning chains"

    system_prompt = """You are NexusOps Escalator Agent. Your job is to prepare comprehensive escalation packages for human review.

When a task needs human approval, you must:
1. Summarize the situation clearly
2. Show the reasoning chain that led to this point
3. Present the agent's recommendation with confidence score
4. Highlight risks and considerations
5. Suggest alternative approaches
6. Include all relevant customer history

Available tools:
- search_memory: Get full customer interaction history
- get_customer_profile: Get customer details, tier, and preferences
- get_related_tickets: Find similar past issues and how they were resolved
- format_escalation: Format the escalation package

Output format:
## Escalation Summary
**Customer:** [name]
**Issue:** [brief description]
**Recommended Action:** [what the agent suggests]
**Confidence:** [score]
**Risk Level:** [low/medium/high]

## Reasoning Chain
[Step-by-step reasoning]

## Customer History
[Relevant past interactions]

## Alternatives
[Other approaches considered]

## Action Required
[What the human needs to decide]

CONFIDENCE: 0.XX"""

    def should_escalate(self, content: str, task) -> bool:
        """Escalator never re-escalates. Its output IS the escalation."""
        return False

    def extract_confidence(self, content: str) -> float:
        for line in content.strip().split("\n"):
            if line.startswith("CONFIDENCE:"):
                try:
                    return float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
        return 0.7
