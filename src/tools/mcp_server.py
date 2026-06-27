"""MCP (Model Context Protocol) server exposing business tools."""

from __future__ import annotations

import json
from typing import Any, Optional

import structlog

logger = structlog.get_logger()


class MCPServer:
    """MCP server that exposes business tools for agents.

    Tools:
    - send_email: Send email via Alibaba Direct Mail
    - read_email: Read inbox messages
    - create_quote: Generate quote PDF
    - schedule_meeting: Calendar management
    - search_crm: Search customer records
    - update_crm: Update customer records
    - search_memory: Semantic memory search
    - store_memory: Save new memory
    - generate_document: Create business documents
    - trigger_webhook: Call external APIs
    - notify_human: Escalate to human
    - get_analytics: Pull business metrics
    """

    def __init__(self, memory_store=None, email_client=None, crm_client=None):
        self.memory = memory_store
        self.email = email_client
        self.crm = crm_client
        self.tools = self._register_tools()

    def _register_tools(self) -> dict:
        """Register all available tools with their handlers."""
        return {
            "send_email": {
                "description": "Send an email to a recipient",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email body (plain text or HTML)"},
                        "attachments": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of file paths to attach",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
                "handler": self._send_email,
            },
            "search_crm": {
                "description": "Search customer records in the CRM database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (name, email, company)"},
                        "limit": {"type": "integer", "description": "Max results to return", "default": 5},
                    },
                    "required": ["query"],
                },
                "handler": self._search_crm,
            },
            "update_crm": {
                "description": "Update customer record in CRM",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Customer ID"},
                        "updates": {"type": "object", "description": "Fields to update"},
                    },
                    "required": ["customer_id", "updates"],
                },
                "handler": self._update_crm,
            },
            "search_memory": {
                "description": "Search past interactions using semantic similarity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "customer_id": {"type": "string", "description": "Filter by customer"},
                        "limit": {"type": "integer", "description": "Max results", "default": 5},
                    },
                    "required": ["query"],
                },
                "handler": self._search_memory,
            },
            "store_memory": {
                "description": "Store a new memory entry",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Memory content"},
                        "category": {"type": "string", "description": "Category (customer, interaction, preference)"},
                        "customer_id": {"type": "string", "description": "Associated customer"},
                    },
                    "required": ["content", "category"],
                },
                "handler": self._store_memory,
            },
            "create_quote": {
                "description": "Generate a quote/proposal document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Customer ID"},
                        "items": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Line items with product, quantity, price",
                        },
                        "validity_days": {"type": "integer", "description": "Quote validity period", "default": 30},
                    },
                    "required": ["customer_id", "items"],
                },
                "handler": self._create_quote,
            },
            "schedule_meeting": {
                "description": "Schedule a meeting with availability check",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Customer ID"},
                        "proposed_times": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Proposed time slots (ISO format)",
                        },
                        "duration_minutes": {"type": "integer", "description": "Meeting duration", "default": 30},
                        "topic": {"type": "string", "description": "Meeting topic"},
                    },
                    "required": ["customer_id", "proposed_times", "topic"],
                },
                "handler": self._schedule_meeting,
            },
            "notify_human": {
                "description": "Escalate task to human with context",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task ID"},
                        "summary": {"type": "string", "description": "Brief summary"},
                        "context": {"type": "object", "description": "Full context package"},
                        "urgency": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    },
                    "required": ["task_id", "summary", "context", "urgency"],
                },
                "handler": self._notify_human,
            },
            "get_customer_profile": {
                "description": "Get customer details and preferences",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string", "description": "Customer ID"},
                    },
                    "required": ["customer_id"],
                },
                "handler": self._get_customer_profile,
            },
        }

    async def _send_email(
        self, to: str, subject: str, body: str, attachments: list[str] = None
    ) -> dict:
        """Send email via Alibaba Direct Mail."""
        # Mock implementation - in production, use aiosmtplib
        logger.info("email_sent", to=to, subject=subject)
        return {
            "status": "sent",
            "message_id": f"msg_{hash(to + subject) % 100000}",
            "to": to,
            "subject": subject,
        }

    async def _search_crm(self, query: str, limit: int = 5) -> dict:
        """Search customer records."""
        # Mock CRM search - in production, query PostgreSQL
        mock_results = [
            {"id": "cust_001", "name": "Acme Corp", "email": "contact@acme.com", "tier": "gold"},
            {"id": "cust_002", "name": "TechStart Inc", "email": "hello@techstart.com", "tier": "silver"},
        ]
        filtered = [r for r in mock_results if query.lower() in r["name"].lower()]
        return {"results": filtered[:limit], "total": len(filtered)}

    async def _update_crm(self, customer_id: str, updates: dict) -> dict:
        """Update customer record."""
        logger.info("crm_updated", customer_id=customer_id, fields=list(updates.keys()))
        return {"status": "updated", "customer_id": customer_id, "updates": updates}

    async def _search_memory(
        self, query: str, customer_id: str = None, limit: int = 5
    ) -> dict:
        """Search memory store."""
        if not self.memory:
            return {"results": [], "error": "Memory store not initialized"}

        results = await self.memory.search(query=query, customer_id=customer_id, limit=limit)
        return {"results": results, "count": len(results)}

    async def _store_memory(
        self, content: str, category: str, customer_id: str = None
    ) -> dict:
        """Store a new memory."""
        if not self.memory:
            return {"error": "Memory store not initialized"}

        from src.memory.store import MemoryEntry
        import time
        import uuid

        entry = MemoryEntry(
            id=str(uuid.uuid4())[:8],
            content=content,
            category=category,
            source_agent="mcp_server",
            customer_id=customer_id,
            created_at=time.time(),
        )
        memory_id = await self.memory.store(entry)
        return {"status": "stored", "memory_id": memory_id}

    async def _create_quote(
        self, customer_id: str, items: list[dict], validity_days: int = 30
    ) -> dict:
        """Generate a quote document."""
        # Mock quote generation - in production, use reportlab for PDF
        total = sum(item.get("quantity", 1) * item.get("price", 0) for item in items)
        quote_id = f"quote_{hash(customer_id + str(total)) % 100000}"
        logger.info("quote_created", quote_id=quote_id, total=total)
        return {
            "quote_id": quote_id,
            "customer_id": customer_id,
            "items": items,
            "total": total,
            "validity_days": validity_days,
            "pdf_url": f"https://oss.aliyuncs.com/quotes/{quote_id}.pdf",
        }

    async def _schedule_meeting(
        self,
        customer_id: str,
        proposed_times: list[str],
        duration_minutes: int = 30,
        topic: str = "",
    ) -> dict:
        """Schedule a meeting."""
        # Mock scheduling - in production, integrate with calendar API
        selected_time = proposed_times[0] if proposed_times else None
        event_id = f"evt_{hash(customer_id + str(selected_time)) % 100000}"
        logger.info("meeting_scheduled", event_id=event_id, time=selected_time)
        return {
            "status": "scheduled",
            "event_id": event_id,
            "customer_id": customer_id,
            "time": selected_time,
            "duration_minutes": duration_minutes,
            "topic": topic,
        }

    async def _notify_human(
        self, task_id: str, summary: str, context: dict, urgency: str
    ) -> dict:
        """Escalate to human reviewer."""
        logger.info("human_escalation", task_id=task_id, urgency=urgency)
        return {
            "status": "escalated",
            "task_id": task_id,
            "urgency": urgency,
            "review_queue_position": 1,
        }

    async def _get_customer_profile(self, customer_id: str) -> dict:
        """Get customer profile."""
        # Mock profile - in production, query CRM database
        return {
            "customer_id": customer_id,
            "name": "Acme Corp",
            "email": "contact@acme.com",
            "tier": "gold",
            "total_interactions": 15,
            "last_contact": "2026-06-25",
            "preferences": {"language": "en", "contact_method": "email"},
        }

    def get_tool_schemas(self) -> list[dict]:
        """Get OpenAI-compatible tool schemas."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for name, tool in self.tools.items()
        ]

    async def execute_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool by name."""
        if name not in self.tools:
            return {"error": f"Unknown tool: {name}"}

        handler = self.tools[name]["handler"]
        try:
            result = await handler(**arguments)
            return result
        except Exception as e:
            logger.error("tool_execution_failed", tool=name, error=str(e))
            return {"error": str(e)}
