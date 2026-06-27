# Building NexusOps: My Journey into Autonomous Business Operations with Qwen Cloud

**Author:** Johnson (AutomatesWithJohnson)
**Hackathon:** Global AI Hackathon Series with Qwen Cloud
**Track:** Track 4 - Autopilot Agent

---

## The Problem That Started It All

Every day, small and medium businesses drown in routine operations. Customer emails pile up. Support tickets go unanswered. Quotes take days to generate. Follow-ups get forgotten.

I have worked with dozens of businesses that lose 40% of their potential revenue simply because they cannot respond fast enough. The human bottleneck is real.

So I asked myself: what if an AI agent could handle 80% of these routine business operations autonomously, and only escalate the critical decisions to humans?

That question became NexusOps.

## Why Qwen Cloud

I evaluated several platforms before choosing Qwen Cloud. Three things made the decision easy.

**Model quality.** Qwen3-Coder-Next delivers reasoning capabilities that rival the best models available. For a business operations agent that needs to understand context, generate quotes, and draft professional responses, this was non-negotiable.

**Function calling.** The OpenAI-compatible API with native tool calling meant I could build a proper agent loop without wrestling with custom parsers. The model calls tools, receives results, and reasons about next steps. This is exactly what an autonomous agent needs.

**Cost.** With 70 million free tokens plus hackathon credits, I could iterate rapidly without burning through budget. Qwen-Plus handles classification tasks at a fraction of the cost, letting me route simple tasks to cheaper models and save the heavy models for complex reasoning.

## Architecture Decisions

### Multi-Agent vs Single Agent

I chose a multi-agent society over a single monolithic agent for three reasons:

1. **Specialization beats generalization.** A classifier agent with a focused system prompt outperforms a generalist agent at classification. Each agent gets optimized for exactly one job.

2. **Failure isolation.** If the Quoter agent fails, the Responder can still draft a response without pricing. A single agent failure does not cascade.

3. **Cost optimization.** The Classifier uses Qwen-Plus (cheap and fast) while the Responder uses Qwen3-Coder-Next (powerful and expensive). Routing simple tasks to cheaper models saves 60% on token costs.

### Memory Architecture

The dual-layer memory system was the hardest design decision.

**Short-term memory (Redis):** Stores the last 24 hours of interactions with a TTL. This handles context for ongoing conversations without polluting long-term storage.

**Long-term memory (PostgreSQL + pgvector):** Stores every interaction with a vector embedding. When a new email arrives from a customer, the agent can search for semantically similar past interactions to understand context.

The key insight was that memory retrieval needs to be fast. Agents cannot wait 5 seconds for a memory search. Redis handles the hot path, and pgvector handles the deep search. Together they give agents both speed and depth.

### Human-in-the-Loop

Full autonomy is a trap. Every agent response includes a confidence score. When confidence drops below 0.7, the system escalates to a human reviewer with a complete context package:

- What happened
- What the agent recommends
- Why the agent is uncertain
- Relevant customer history

This is not a compromise. It is a feature. The system learns from human decisions and stores them in memory, improving future confidence scores.

## Building with Qwen Models

### Function Calling

The function calling support was the biggest pleasant surprise. Qwen models understand tool schemas, generate proper JSON arguments, and process tool results in subsequent turns. The OpenAI-compatible API meant I could use the standard Python SDK without custom adapters.

```python
response = await client.chat.completions.create(
    model="qwen-plus",
    messages=messages,
    tools=tool_schemas,
    tool_choice="auto",
)
# Model decides which tools to call, executes them,
# and returns final response with tool results incorporated
```

### Streaming

Streaming responses are essential for the dashboard. Users see agent responses as they are generated, not after a 10-second wait. Qwen streaming works flawlessly with the standard OpenAI streaming pattern.

### Embeddings

The text-embedding-v3 model generates 1024-dimensional vectors that power semantic memory search. When a customer emails about "enterprise pricing", the memory layer finds past interactions about "premium plans" and "corporate rates" because they are semantically similar, even if the exact words differ.

## Challenges

### Context Window Management

Five agents, each with memory context, tool schemas, and conversation history, can easily exceed context limits. I solved this with:

- Limiting memory retrieval to 5 most relevant entries per agent
- Truncating tool results to essential fields only
- Using the fast model for classification to keep that context window lean

### Token Budget

With 70 million free tokens, budget seems unlimited until you start building. A single end-to-end event can consume 5,000-10,000 tokens across all agents. At that rate, 70 million tokens handle about 7,000-14,000 events. Enough for development and demo, but production use needs careful model routing.

### Latency

A multi-agent chain with 5 agents can take 15-20 seconds end-to-end. I optimized by:

- Running the Classifier agent first (fast, cheap)
- Only activating necessary downstream agents
- Parallelizing independent tool calls within agents
- Using Qwen-Plus for structured tasks that do not need heavy reasoning

## What I Would Do Differently

1. **Start with fewer agents.** Build Classifier + Responder first. Get that working end-to-end before adding more agents.

2. **Mock everything first.** Build with mock data, validate the architecture, then connect real APIs. I wasted time debugging API connections before the architecture was solid.

3. **Invest in observability earlier.** Structured logging from day one would have saved hours of debugging.

## What Comes Next

NexusOps is a working prototype. For production, I would add:

- **Real email integration** via Alibaba Direct Mail
- **Real CRM backend** with customer database
- **PDF generation** with ReportLab for professional quotes
- **Calendar API** integration for scheduling
- **Webhook system** for connecting to existing business tools
- **A/B testing** different agent prompts and model combinations

## Final Thoughts

Building NexusOps taught me that the hardest part of autonomous agents is not the AI. It is the engineering around it: memory management, error handling, human escalation, and cost optimization.

Qwen Cloud gave me the right foundation. The models are capable, the API is clean, and the pricing is fair. For anyone building production AI agents, this platform deserves serious consideration.

The future of business operations is not humans replaced by AI. It is humans empowered by AI agents that handle the routine, surface the important, and escalate the critical. NexusOps is my step toward that future.

---

**Repository:** https://github.com/AutomatesWithJohnson/nexusops
**Architecture Diagram:** https://github.com/AutomatesWithJohnson/nexusops/blob/main/docs/architecture-diagram.html
**Demo Scenario:** https://github.com/AutomatesWithJohnson/nexusops/blob/main/scripts/demo_scenario.py
