# NexusOps - Autonomous Business Operations Agent

An AI-powered multi-agent system that automates the full customer lifecycle, from inquiry email to quote generation, follow-up scheduling, and support resolution. Built with Qwen models on Alibaba Cloud.

## Features

- **Intelligent Classification:** Automatically categorizes inbound customer messages (sales, support, complaints, partnerships)
- **Autonomous Response:** Drafts contextual responses using persistent customer memory
- **Quote Generation:** Creates professional quotes and proposals from product catalogs
- **Smart Scheduling:** Manages calendars and follow-up reminders
- **Human-in-the-Loop:** Escalates critical decisions with full context and reasoning chains
- **Persistent Memory:** Cross-session memory with semantic search, relevance decay, and customer profiles
- **Multi-Agent Coordination:** 5 specialized agents working together through task delegation and conflict resolution

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Orchestrator                       │
│            (Task routing + coordination)              │
├──────┬──────┬──────┬──────┬─────────────────────────┤
│Class-│Respon│Quoter│Sched-│Escalator                │
│ifier │der   │      │uler  │                         │
│Agent │Agent │Agent │Agent │Agent                    │
├──────┴──────┴──────┴──────┴─────────────────────────┤
│              Memory Layer                            │
│     Redis (short-term) + PostgreSQL+pgvector         │
├──────────────────────────────────────────────────────┤
│              MCP Tool Server                         │
│  email | calendar | CRM | documents | webhooks       │
├──────────────────────────────────────────────────────┤
│           Alibaba Cloud Infrastructure               │
│  ECS | RDS | Tair | OSS | Function Compute | Model   │
│  Studio (Qwen)                                       │
└──────────────────────────────────────────────────────┘
```

## Track

**Track 4: Autopilot Agent** (with elements of Track 1: MemoryAgent and Track 3: Agent Society)

## Quick Start

```bash
# Clone
git clone https://github.com/AutomatesWithJohnson/nexusops.git
cd nexusops

# Setup
python -m venv venv
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys

# Run locally
docker-compose up -d  # Start Redis + PostgreSQL
python -m src.main

# Dashboard
streamlit run src/dashboard/app.py
```

## Tech Stack

- **Models:** Qwen3-Coder-Next, Qwen3-VL-Plus, Qwen-Plus (via Model Studio)
- **Backend:** Python 3.11, FastAPI
- **Database:** PostgreSQL + pgvector, Redis/Tair
- **Infrastructure:** Alibaba Cloud ECS, OSS, Function Compute
- **Dashboard:** Streamlit
- **Protocols:** Model Context Protocol (MCP)

## License

MIT
