"""NexusOps - Autonomous Business Operations Agent.

FastAPI application entry point.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.orchestrator import Orchestrator
from src.memory.store import MemoryStore


# Global instances
orchestrator = Orchestrator()
memory_store = MemoryStore()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await memory_store.setup()
    await _register_agents()
    yield
    # Shutdown
    await memory_store.close()


app = FastAPI(
    title="NexusOps",
    description="Autonomous Business Operations Agent powered by Qwen",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _register_agents():
    """Register all agents with the orchestrator."""
    from src.agents.classifier import ClassifierAgent
    from src.agents.responder import ResponderAgent
    from src.agents.quoter import QuoterAgent
    from src.agents.scheduler import SchedulerAgent
    from src.agents.escalator import EscalatorAgent

    agents = [
        ClassifierAgent(memory_store=memory_store),
        ResponderAgent(memory_store=memory_store),
        QuoterAgent(memory_store=memory_store),
        SchedulerAgent(memory_store=memory_store),
        EscalatorAgent(memory_store=memory_store),
    ]
    for agent in agents:
        orchestrator.register_agent(agent)


@app.get("/")
async def root():
    return {
        "name": "NexusOps",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/status")
async def status():
    return orchestrator.get_status()


@app.post("/events/{event_type}")
async def process_event(event_type: str, payload: dict):
    """Process an inbound business event."""
    result = await orchestrator.process_event(event_type, payload)
    return {
        "task_id": result.task_id,
        "agent_chain": result.agent_chain,
        "response": result.final_response.content if result.final_response else None,
        "confidence": result.final_response.confidence if result.final_response else 0,
        "escalated": result.escalated,
        "latency_ms": round(result.total_latency_ms, 2),
    }


@app.get("/human-queue")
async def get_human_queue():
    """Get pending human review tasks."""
    return orchestrator.pending_human_tasks


@app.post("/human-queue/{task_id}/review")
async def review_task(task_id: str, approved: bool, modifications: dict = None):
    """Approve or reject a human review task."""
    result = await orchestrator.approve_human_task(task_id, approved, modifications)
    return result or {"error": "Task not found"}


@app.get("/memory/{customer_id}")
async def get_customer_memory(customer_id: str, limit: int = 10):
    """Get memory context for a customer."""
    context = await memory_store.get_customer_context(customer_id, limit)
    return context
