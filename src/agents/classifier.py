"""Classifier Agent - categorizes inbound messages."""

from src.core.agent_base import BaseAgent
from src.config import settings


class ClassifierAgent(BaseAgent):
    name = "classifier"
    model = settings.model_fast  # Qwen-Plus: fast and cheap for classification
    description = "Classifies inbound business messages into categories"

    system_prompt = """You are NexusOps Classifier Agent. Your job is to analyze inbound business messages and classify them into exactly one category.

Categories:
- sales_inquiry: Customer asking about products, pricing, or requesting a quote
- support_ticket: Customer reporting a problem, bug, or needing technical help
- complaint: Customer expressing dissatisfaction or frustration
- partnership: Business partnership or collaboration inquiry
- follow_up: Reminder or follow-up for a previous interaction
- spam: Irrelevant, promotional, or malicious content
- other: Anything that doesn't fit the above categories

Rules:
1. Always respond with the category name first, then a brief explanation
2. Format: "CATEGORY: explanation"
3. If the message is ambiguous, classify based on the most likely intent
4. Flag any urgent language (e.g., "ASAP", "emergency", "critical") in the explanation

You do NOT need tools. Just classify and explain."""

    def extract_confidence(self, content: str) -> float:
        """High confidence for clear classifications, lower for ambiguous ones."""
        if content.startswith(("sales_inquiry", "support_ticket", "complaint")):
            return 0.95
        elif "spam" in content.lower():
            return 0.9
        else:
            return 0.7

    def should_escalate(self, content: str, task) -> bool:
        """Never escalate from classifier. Let downstream agents decide."""
        return False
