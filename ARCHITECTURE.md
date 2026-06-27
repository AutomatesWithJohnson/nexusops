# NexusOps Architecture

## System Overview

NexusOps is a multi-agent autonomous business operations system that processes customer interactions end-to-end without human intervention, escalating only when confidence is low or decisions require human judgment.

## Architecture Pattern

**Multi-Agent Society with Central Orchestrator**

The system follows a hub-and-spoke pattern where a central orchestrator receives all inbound events, classifies them, and routes tasks to specialized agents. Each agent operates independently with its own model, tools, and system prompt, but shares a common memory layer.

## Components

### 1. FastAPI Gateway (`src/main.py`)

The entry point for all inbound events. Exposes REST endpoints and WebSocket connections for real-time dashboard updates.

**Endpoints:**
- `POST /events/{event_type}` - Process inbound business event
- `GET /status` - System health and agent status
- `GET /human-queue` - Pending human review tasks
- `POST /human-queue/{task_id}/review` - Approve/reject task
- `GET /memory/{customer_id}` - Customer memory context

### 2. Orchestrator (`src/core/orchestrator.py`)

The brain of the system. Responsibilities:
- Receive and classify inbound events
- Route tasks to appropriate agent chains
- Manage multi-agent coordination
- Handle human-in-the-loop checkpoints
- Log all actions for audit trail

**Routing Logic:**
| Classification | Agent Chain |
|---|---|
| sales_inquiry | Quoter → Responder |
| support_ticket | Responder |
| complaint | Responder → Escalator |
| follow_up | Scheduler |
| partnership | Responder → Escalator |
| spam | (no action) |

### 3. Base Agent Framework (`src/core/agent_base.py`)

All agents inherit from `BaseAgent` which provides:
- OpenAI-compatible Qwen client with retry logic
- Tool calling loop (up to `max_agent_iterations`)
- Memory integration (read relevant past interactions)
- Confidence extraction from responses
- Escalation logic based on confidence thresholds
- Status reporting and statistics tracking

**Agent Lifecycle:**
```
Task → Build messages (system + memory + task)
     → Call model (with tool schemas)
     → If tool_calls → execute tools → loop
     → If text response → check confidence → return or escalate
```

### 4. Specialized Agents (`src/agents/`)

#### Classifier Agent
- **Model:** Qwen-Plus (fast, cheap)
- **Job:** Categorize messages into 7 types
- **Tools:** None (pure classification)
- **Output:** Category + explanation

#### Responder Agent
- **Model:** Qwen3-Coder-Next (quality responses)
- **Job:** Draft contextual customer responses
- **Tools:** search_memory, get_customer_profile, draft_email
- **Output:** Draft email + confidence score

#### Quoter Agent
- **Model:** Qwen3-Coder-Next (complex reasoning)
- **Job:** Generate quotes and proposals
- **Tools:** get_catalog, calculate_price, search_memory, generate_quote_pdf
- **Output:** Quote document + pricing summary

#### Scheduler Agent
- **Model:** Qwen-Plus (structured task)
- **Job:** Manage calendars and follow-ups
- **Tools:** check_availability, create_event, set_reminder, send_invite
- **Output:** Scheduled event + confirmation

#### Escalator Agent
- **Model:** Qwen3-Coder-Next (reasoning about context)
- **Job:** Prepare human review packages
- **Tools:** search_memory, get_customer_profile, get_related_tickets
- **Output:** Full escalation package with reasoning chain

### 5. Memory Layer (`src/memory/store.py`)

Dual-layer persistent memory:

**Redis/Tair (Short-term):**
- Current conversation context
- Recent interactions (last 24 hours, TTL)
- Active task state
- Customer timeline (last 100 interactions)
- Customer preferences (hash map)

**PostgreSQL + pgvector (Long-term):**
- All interactions with vector embeddings
- Customer profiles
- Semantic search across entire history
- Memory relevance scoring with decay

**Memory Operations:**
- `store()` - Save to both Redis and PostgreSQL
- `search()` - Semantic similarity search via pgvector
- `get_customer_context()` - Full context for a customer

### 6. MCP Tool Server (`src/tools/mcp_server.py`)

Exposes 9 business tools following the Model Context Protocol:

| Tool | Description |
|---|---|
| send_email | Send email via Alibaba Direct Mail |
| search_crm | Search customer records |
| update_crm | Update customer record |
| search_memory | Semantic memory search |
| store_memory | Save new memory entry |
| create_quote | Generate quote PDF |
| schedule_meeting | Calendar management |
| notify_human | Escalate to human |
| get_customer_profile | Get customer details |

### 7. Streamlit Dashboard (`src/dashboard/app.py`)

Real-time monitoring interface with 5 pages:
- **Overview:** System metrics, event charts, latency distribution
- **Agents:** Per-agent performance, status, error rates
- **Memory:** Search interface, statistics, browse entries
- **Events:** Filterable event log with full audit trail
- **Human Queue:** Pending approvals with approve/reject actions

## Data Flow

```
Inbound Event (email/webhook/API)
    ↓
FastAPI Gateway
    ↓
Orchestrator
    ├── Classifier Agent → "sales_inquiry"
    ├── Quoter Agent → generates quote
    ├── Responder Agent → drafts reply
    ├── Scheduler Agent → sets follow-up
    └── Escalator Agent → (if needed)
    ↓
Memory Layer (store results)
    ↓
Response sent + Dashboard updated
```

## Infrastructure

| Service | Alibaba Cloud Product | Purpose |
|---|---|---|
| Compute | ECS (2C4G) | Application hosting |
| AI Models | Model Studio | Qwen3-Coder-Next, Qwen-Plus, embeddings |
| Database | RDS PostgreSQL | Long-term memory + pgvector |
| Cache | Tair/Redis | Short-term memory + session state |
| Storage | OSS | Document/quote PDF storage |
| Email | Direct Mail | Outbound email delivery |
| Container | ACK (optional) | Kubernetes orchestration |

## Security

- API keys stored in environment variables (never in code)
- Human-in-the-loop for all critical decisions
- Full audit trail of every agent action
- Customer data encrypted at rest
- Rate limiting on API endpoints
- Memory decay removes stale customer data over time

## Error Handling

- **Agent timeout:** Falls back to escalation after max iterations
- **Model API failure:** Retry with exponential backoff (3 attempts)
- **Tool failure:** Logged and reported in agent response
- **Memory failure:** Graceful degradation (agents work without memory)
- **Database failure:** Redis-only mode (short-term memory only)

## Scalability

- Horizontal: Add more agent instances behind a load balancer
- Vertical: Upgrade ECS instance for more concurrent tasks
- Database: PostgreSQL read replicas for search queries
- Cache: Redis Cluster for high availability
