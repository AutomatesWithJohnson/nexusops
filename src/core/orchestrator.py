"""Central orchestrator that routes tasks to specialized agents."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

import structlog

from src.config import settings
from src.core.agent_base import (
    AgentResponse,
    AgentStatus,
    BaseAgent,
    Task,
    TaskPriority,
)

logger = structlog.get_logger()


@dataclass
class OrchestrationResult:
    """Result of orchestrating a task through the agent system."""
    task_id: str
    agent_chain: list[str] = field(default_factory=list)
    responses: list[AgentResponse] = field(default_factory=list)
    final_response: Optional[AgentResponse] = None
    total_latency_ms: float = 0.0
    escalated: bool = False


class Orchestrator:
    """Routes inbound events to the right agent(s) and coordinates multi-agent workflows.

    Responsibilities:
    1. Receive inbound events (emails, webhooks, API calls)
    2. Classify the event using the Classifier agent
    3. Route to specialized agent(s) based on classification
    4. Coordinate multi-agent workflows when needed
    5. Manage human-in-the-loop checkpoints
    6. Record all actions to memory
    """

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self.pending_human_tasks: list[dict] = []
        self.event_log: list[dict] = []

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.name] = agent
        logger.info("agent_registered", agent=agent.name, model=agent.model)

    def get_agent(self, name: str) -> BaseAgent:
        """Get a registered agent by name."""
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not registered")
        return self.agents[name]

    async def process_event(self, event_type: str, payload: dict) -> OrchestrationResult:
        """Process an inbound event end-to-end.

        Flow:
        1. Classify the event
        2. Route to appropriate agent(s)
        3. Execute the task(s)
        4. Handle escalation if needed
        5. Log everything
        """
        task_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        result = OrchestrationResult(task_id=task_id)

        logger.info(
            "event_received",
            task_id=task_id,
            event_type=event_type,
            payload_keys=list(payload.keys()),
        )

        # Step 1: Classify
        classifier = self.get_agent("classifier")
        classify_task = Task(
            id=task_id,
            type="classify",
            payload={"event_type": event_type, **payload},
        )
        classification = await classifier.reason(classify_task)
        result.agent_chain.append("classifier")
        result.responses.append(classification)

        # Step 2: Route based on classification
        route = self._determine_route(classification.content)
        logger.info("task_routed", task_id=task_id, route=route)

        # Step 3: Execute with specialized agent(s)
        for agent_name in route:
            agent = self.get_agent(agent_name)
            task = Task(
                id=task_id,
                type=agent_name,
                priority=self._classify_priority(classification.content, payload),
                payload=payload,
                context={"classification": classification.content},
            )
            response = await agent.reason(task)
            result.agent_chain.append(agent_name)
            result.responses.append(response)

            # Check if escalation needed
            if response.needs_human:
                result.escalated = True
                self._queue_human_review(task_id, agent_name, response, payload)
                break

            # If agent signals a next action, continue the chain
            if response.next_action and response.next_action in self.agents:
                continue

        # Step 4: Compile final response
        result.final_response = result.responses[-1] if result.responses else None
        result.total_latency_ms = (time.time() - start_time) * 1000

        # Step 5: Log the event
        self._log_event(task_id, event_type, result)

        logger.info(
            "event_completed",
            task_id=task_id,
            agents=result.agent_chain,
            latency_ms=round(result.total_latency_ms, 2),
            escalated=result.escalated,
        )

        return result

    def _determine_route(self, classification: str) -> list[str]:
        """Determine which agent(s) to route to based on classification."""
        classification_lower = classification.lower()

        if "sales" in classification_lower or "inquiry" in classification_lower:
            return ["quoter", "responder"]
        elif "support" in classification_lower or "ticket" in classification_lower:
            return ["responder"]
        elif "complaint" in classification_lower:
            return ["responder", "escalator"]
        elif "follow" in classification_lower or "reminder" in classification_lower:
            return ["scheduler"]
        elif "partnership" in classification_lower:
            return ["responder", "escalator"]
        elif "spam" in classification_lower:
            return []  # No action needed
        else:
            return ["responder"]  # Default fallback

    def _classify_priority(self, classification: str, payload: dict) -> TaskPriority:
        """Determine task priority from classification and payload."""
        classification_lower = classification.lower()
        if "urgent" in classification_lower or "critical" in classification_lower:
            return TaskPriority.CRITICAL
        elif "complaint" in classification_lower:
            return TaskPriority.HIGH
        elif "spam" in classification_lower:
            return TaskPriority.LOW
        return TaskPriority.NORMAL

    def _queue_human_review(
        self, task_id: str, agent_name: str, response: AgentResponse, payload: dict
    ):
        """Queue a task for human review."""
        review = {
            "task_id": task_id,
            "agent": agent_name,
            "response": response.content,
            "confidence": response.confidence,
            "payload": payload,
            "created_at": time.time(),
            "status": "pending",
        }
        self.pending_human_tasks.append(review)
        logger.info("human_review_queued", task_id=task_id, agent=agent_name)

    def _log_event(self, task_id: str, event_type: str, result: OrchestrationResult):
        """Log an event for audit trail."""
        self.event_log.append({
            "task_id": task_id,
            "event_type": event_type,
            "agent_chain": result.agent_chain,
            "latency_ms": result.total_latency_ms,
            "escalated": result.escalated,
            "timestamp": time.time(),
        })

    async def approve_human_task(self, task_id: str, approved: bool, modifications: dict = None):
        """Approve or reject a human review task."""
        for task in self.pending_human_tasks:
            if task["task_id"] == task_id:
                task["status"] = "approved" if approved else "rejected"
                task["reviewed_at"] = time.time()
                task["modifications"] = modifications
                logger.info(
                    "human_review_completed",
                    task_id=task_id,
                    approved=approved,
                )
                return task
        return None

    def get_status(self) -> dict:
        """Get orchestrator status overview."""
        return {
            "agents": {name: agent.get_status() for name, agent in self.agents.items()},
            "pending_human_tasks": len(self.pending_human_tasks),
            "total_events_processed": len(self.event_log),
        }
