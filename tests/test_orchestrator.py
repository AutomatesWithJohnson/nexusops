"""Tests for the orchestrator."""

import pytest
from src.core.orchestrator import Orchestrator
from src.core.agent_base import AgentResponse, Task, TaskPriority


@pytest.mark.asyncio
async def test_orchestrator_registers_agents():
    """Test that orchestrator can register agents."""
    orchestrator = Orchestrator()

    # Mock agent
    class MockAgent:
        name = "test_agent"
        model = "qwen-plus"
        def get_status(self):
            return {"name": self.name, "status": "idle"}

    agent = MockAgent()
    orchestrator.register_agent(agent)

    assert "test_agent" in orchestrator.agents
    assert orchestrator.get_agent("test_agent") == agent


@pytest.mark.asyncio
async def test_orchestrator_determines_route():
    """Test route determination based on classification."""
    orchestrator = Orchestrator()

    # Sales inquiry should route to quoter and responder
    route = orchestrator._determine_route("sales_inquiry: Customer asking about pricing")
    assert "quoter" in route or "responder" in route

    # Support ticket should route to responder
    route = orchestrator._determine_route("support_ticket: Technical issue reported")
    assert "responder" in route

    # Spam should route nowhere
    route = orchestrator._determine_route("spam: Irrelevant content")
    assert len(route) == 0


@pytest.mark.asyncio
async def test_orchestrator_classifies_priority():
    """Test priority classification."""
    orchestrator = Orchestrator()

    # Urgent language should be critical
    priority = orchestrator._classify_priority("urgent: System down", {})
    assert priority == TaskPriority.CRITICAL

    # Complaint should be high
    priority = orchestrator._classify_priority("complaint: Very unhappy", {})
    assert priority == TaskPriority.HIGH

    # Spam should be low
    priority = orchestrator._classify_priority("spam: Buy now", {})
    assert priority == TaskPriority.LOW

    # Default should be normal
    priority = orchestrator._classify_priority("sales_inquiry: Question", {})
    assert priority == TaskPriority.NORMAL


@pytest.mark.asyncio
async def test_orchestrator_queues_human_review():
    """Test human review queue."""
    orchestrator = Orchestrator()

    response = AgentResponse(
        content="Test response",
        confidence=0.6,
        needs_human=True,
    )

    orchestrator._queue_human_review("task_001", "responder", response, {"text": "test"})

    assert len(orchestrator.pending_human_tasks) == 1
    assert orchestrator.pending_human_tasks[0]["task_id"] == "task_001"
    assert orchestrator.pending_human_tasks[0]["agent"] == "responder"


@pytest.mark.asyncio
async def test_orchestrator_approves_human_task():
    """Test human task approval."""
    orchestrator = Orchestrator()

    # Add a pending task
    orchestrator.pending_human_tasks.append({
        "task_id": "task_001",
        "agent": "responder",
        "response": "Test",
        "status": "pending",
    })

    # Approve it
    result = await orchestrator.approve_human_task("task_001", approved=True)

    assert result["status"] == "approved"
    assert "reviewed_at" in result


@pytest.mark.asyncio
async def test_orchestrator_get_status():
    """Test status reporting."""
    orchestrator = Orchestrator()

    class MockAgent:
        name = "test"
        model = "qwen-plus"
        def get_status(self):
            return {"name": self.name, "status": "idle", "stats": {}}

    orchestrator.register_agent(MockAgent())

    status = orchestrator.get_status()

    assert "agents" in status
    assert "test" in status["agents"]
    assert "pending_human_tasks" in status
    assert "total_events_processed" in status
