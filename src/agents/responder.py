"""Responder Agent - drafts contextual responses using memory."""

from src.core.agent_base import BaseAgent
from src.config import settings


class ResponderAgent(BaseAgent):
    name = "responder"
    model = settings.model_reasoning  # Qwen3-Coder-Next for quality responses
    description = "Drafts contextual customer responses using memory and context"

    system_prompt = """You are NexusOps Responder Agent. Your job is to draft professional, helpful responses to customer messages.

Guidelines:
1. Always be professional, empathetic, and clear
2. Use customer history from memory to personalize responses
3. Reference past interactions when relevant
4. Match the customer's language (English by default)
5. Keep responses concise but thorough
6. For complaints: acknowledge the issue, apologize, propose solution
7. For support: diagnose based on history, provide clear steps
8. For inquiries: provide relevant info, suggest next steps

Available tools:
- search_memory: Search past interactions with this customer
- get_customer_profile: Get customer details and preferences
- draft_email: Format and validate the email draft

End your response with a confidence score (0.0-1.0) on a new line:
CONFIDENCE: 0.XX"""

    def extract_confidence(self, content: str) -> float:
        """Extract confidence from the CONFIDENCE line."""
        for line in content.strip().split("\n"):
            if line.startswith("CONFIDENCE:"):
                try:
                    return float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
        return 0.75

    def should_escalate(self, content: str, task) -> bool:
        """Escalate if confidence is below threshold."""
        confidence = self.extract_confidence(content)
        return confidence < settings.human_approval_threshold
