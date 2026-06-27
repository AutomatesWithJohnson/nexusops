"""Base agent class for all NexusOps agents."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AgentStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING_HUMAN = "waiting_human"
    ERROR = "error"


@dataclass
class Task:
    """A unit of work for an agent."""
    id: str
    type: str
    priority: TaskPriority = TaskPriority.NORMAL
    payload: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Output from an agent's reasoning."""
    content: str
    confidence: float = 1.0
    tool_calls_made: list = field(default_factory=list)
    memory_updates: list = field(default_factory=list)
    next_action: Optional[str] = None
    needs_human: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolCall:
    """Represents a tool call made during reasoning."""
    name: str
    arguments: dict
    result: Any
    duration_ms: float


class BaseAgent(ABC):
    """Base class for all NexusOps agents.

    Every agent:
    - Inherits system prompt from its class
    - Uses a specific Qwen model
    - Has access to a defined set of tools
    - Can read/write from the memory store
    - Logs all actions for audit
    """

    name: str = "base"
    model: str = settings.model_fast
    description: str = "Base agent"
    system_prompt: str = "You are a helpful AI agent."

    def __init__(self, memory_store=None, tool_registry=None):
        self.memory = memory_store
        self.tools = tool_registry or {}
        self.status = AgentStatus.IDLE
        self.stats = {"tasks_completed": 0, "errors": 0, "avg_latency_ms": 0}
        self.client = AsyncOpenAI(
            base_url=settings.dashscope_base_url,
            api_key=settings.dashscope_api_key,
        )

    def get_tool_schemas(self) -> list[dict]:
        """Return OpenAI-compatible tool schemas for this agent."""
        schemas = []
        for name, tool in self.tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            })
        return schemas

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def _call_model(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> Any:
        """Call Qwen model with retry logic."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**kwargs)
        return response

    async def execute_tool_call(self, tool_call) -> dict:
        """Execute a single tool call and return the result."""
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            args = {}

        start = time.time()
        if name in self.tools:
            handler = self.tools[name]["handler"]
            result = await handler(**args)
        else:
            result = {"error": f"Unknown tool: {name}"}

        duration = (time.time() - start) * 1000
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, default=str),
            "_meta": ToolCall(name=name, arguments=args, result=result, duration_ms=duration),
        }

    async def reason(self, task: Task) -> AgentResponse:
        """Core reasoning loop with tool calling.

        Sends the task to the model, executes any tool calls,
        and loops until the model produces a final text response.
        """
        self.status = AgentStatus.WORKING
        start_time = time.time()
        tool_calls_log = []

        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        # Inject relevant memories
        if self.memory:
            memories = await self.memory.search(
                query=task.payload.get("text", ""),
                limit=5,
            )
            if memories:
                memory_text = "\n".join(
                    f"- {m['content']} (relevance: {m['score']:.2f})"
                    for m in memories
                )
                messages.append({
                    "role": "system",
                    "content": f"Relevant past interactions:\n{memory_text}",
                })

        # Add the task as user message
        messages.append({
            "role": "user",
            "content": self.format_task(task),
        })

        tool_schemas = self.get_tool_schemas()
        iterations = 0

        while iterations < settings.max_agent_iterations:
            iterations += 1
            response = await self._call_model(messages, tools=tool_schemas or None)
            choice = response.choices[0]

            # Model wants to call tools
            if choice.message.tool_calls:
                messages.append(choice.message.model_dump())
                for tc in choice.message.tool_calls:
                    result = await self.execute_tool_call(tc)
                    tool_calls_log.append(result.get("_meta"))
                    # Remove _meta before sending back to model
                    clean_result = {k: v for k, v in result.items() if k != "_meta"}
                    messages.append(clean_result)
                continue

            # Model produced final text response
            content = choice.message.content or ""
            latency = (time.time() - start_time) * 1000
            self.status = AgentStatus.IDLE
            self.stats["tasks_completed"] += 1
            self.stats["avg_latency_ms"] = (
                (self.stats["avg_latency_ms"] * (self.stats["tasks_completed"] - 1) + latency)
                / self.stats["tasks_completed"]
            )

            # Check if response needs human approval
            needs_human = self.should_escalate(content, task)

            return AgentResponse(
                content=content,
                confidence=self.extract_confidence(content),
                tool_calls_made=tool_calls_log,
                needs_human=needs_human,
                metadata={
                    "iterations": iterations,
                    "latency_ms": latency,
                    "model": self.model,
                },
            )

        # Max iterations reached
        self.status = AgentStatus.ERROR
        self.stats["errors"] += 1
        return AgentResponse(
            content="Agent reached maximum iteration limit. Escalating to human.",
            confidence=0.0,
            needs_human=True,
            tool_calls_made=tool_calls_log,
        )

    def format_task(self, task: Task) -> str:
        """Format a task into a user message. Override in subclasses."""
        parts = [f"Task type: {task.type}"]
        if task.payload:
            parts.append(f"Details:\n{json.dumps(task.payload, indent=2, default=str)}")
        if task.context:
            parts.append(f"Context:\n{json.dumps(task.context, indent=2, default=str)}")
        return "\n\n".join(parts)

    def extract_confidence(self, content: str) -> float:
        """Extract confidence score from response. Override in subclasses."""
        return 0.8

    def should_escalate(self, content: str, task: Task) -> bool:
        """Determine if this response needs human approval."""
        if task.priority == TaskPriority.CRITICAL:
            return True
        return False

    def get_status(self) -> dict:
        """Return current agent status and stats."""
        return {
            "name": self.name,
            "status": self.status.value,
            "model": self.model,
            "stats": self.stats,
        }
