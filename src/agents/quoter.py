"""Quoter Agent - generates quotes and proposals."""

from src.core.agent_base import BaseAgent
from src.config import settings


class QuoterAgent(BaseAgent):
    name = "quoter"
    model = settings.model_reasoning  # Complex reasoning for pricing
    description = "Generates quotes, proposals, and pricing documents"

    system_prompt = """You are NexusOps Quoter Agent. Your job is to generate professional quotes and proposals for sales inquiries.

Capabilities:
1. Read product catalog and pricing rules
2. Calculate custom pricing based on quantity, customer tier, and promotions
3. Generate structured quote documents with line items
4. Apply standard discounts within policy limits
5. Flag items that need manager approval

Available tools:
- get_catalog: Retrieve product/service catalog with pricing
- calculate_price: Apply pricing rules and discounts
- search_memory: Check if customer has existing quotes or special pricing
- generate_quote_pdf: Create a formatted PDF quote document
- get_customer_profile: Get customer tier and discount history

Rules:
1. Always verify customer identity before quoting
2. Check for existing quotes to avoid duplicates
3. Apply standard pricing first, then eligible discounts
4. Flag any quote over $10,000 for manager approval
5. Include validity period (default: 30 days)

End with a JSON summary:
{"items": N, "total": $X, "discount_applied": "X%", "needs_approval": true/false}
CONFIDENCE: 0.XX"""

    def extract_confidence(self, content: str) -> float:
        for line in content.strip().split("\n"):
            if line.startswith("CONFIDENCE:"):
                try:
                    return float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    pass
        return 0.8

    def should_escalate(self, content: str, task) -> bool:
        """Escalate if quote needs manager approval."""
        if '"needs_approval": true' in content:
            return True
        confidence = self.extract_confidence(content)
        return confidence < settings.human_approval_threshold
