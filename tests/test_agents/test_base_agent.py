"""Tests for the base agent."""

import pytest
from src.core.agent_base import BaseAgent, Task, AgentResponse, TaskPriority


class TestAgent(BaseAgent):
    """Test agent implementation."""
    name = "test"
    model = "qwen-plus"
    system_prompt = "You are a test agent."


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes correctly."""
    agent = TestAgent()

    assert agent.name == "test"
    assert agent.model == "qwen-plus"
    assert agent.status.value == "idle"
    assert agent.stats["tasks_completed"] == 0


@pytest.mark.asyncio
async def test_agent_formats_task():
    """Test task formatting."""
    agent = TestAgent()

    task = Task(
        id="task_001",
        type="test",
        payload={"text": "Hello world"},
        context={"customer_id": "cust_001"},
    )

    formatted = agent.format_task(task)

    assert "test" in formatted
    assert "Hello world" in formatted
    assert "cust_001" in formatted


@pytest.mark.asyncio
async def test_agent_extracts_confidence():
    """Test confidence extraction (default implementation)."""
    agent = TestAgent()

    # Default implementation returns 0.8
    confidence = agent.extract_confidence("Some response")
    assert confidence == 0.8


@pytest.mark.asyncio
async def test_agent_should_escalate():
    """Test escalation logic."""
    agent = TestAgent()

    task_normal = Task(id="1", type="test", priority=TaskPriority.NORMAL)
    task_critical = Task(id="2", type="test", priority=TaskPriority.CRITICAL)

    # Normal tasks don't escalate
    assert not agent.should_escalate("response", task_normal)

    # Critical tasks always escalate
    assert agent.should_escalate("response", task_critical)


@pytest.mark.asyncio
async def test_agent_get_status():
    """Test status reporting."""
    agent = TestAgent()

    status = agent.get_status()

    assert status["name"] == "test"
    assert status["status"] == "idle"
    assert status["model"] == "qwen-plus"
    assert "stats" in status
