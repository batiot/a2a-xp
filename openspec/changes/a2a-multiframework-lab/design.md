## Context

Greenfield monorepo. No existing code — everything is new. The project is a personal learning lab comparing three A2A-capable agent frameworks (AG2/FastAgency, CrewAI, LangGraph Agent Server) by implementing the exact same demo agent in each, then validating them with a shared A2A test client. All three agents must be startable independently via Docker and composable together via a root `docker-compose.yml`.

The demo agent task is: given a partial French children's rhyme ("3 petits chats / qui mangeaient des rats..."), return the next line. This is intentionally trivial — it tests A2A protocol plumbing, not agent intelligence.

Non-commercial, personal use. Python 3.12 throughout.

## Goals / Non-Goals

**Goals:**
- Each sub-project is self-contained and independently runnable (`docker compose up` in `agents/<name>/`)
- All three expose a valid A2A `/.well-known/agent.json` card
- All three accept A2A tasks and return streaming (SSE) or synchronous responses
- Shared infra (postgres, redis) lives in `infra/` and is referenced by LangGraph only
- A test client in `client/` sends the same rhyme prompt to all three and prints responses side-by-side
- Root `docker-compose.yml` uses `include:` to compose everything with named profiles

**Non-Goals:**
- Production deployment (no TLS, no auth hardening, no autoscaling)
- Complex multi-step agent reasoning (the demo is intentionally simple)
- GUI / frontend
- LangSmith cloud integration (strictly self-hosted)
- Supporting frameworks other than the three chosen

## Decisions

### D1 — Monorepo structure: Option B (independent sub-projects)

Each framework has different Python dependency trees (especially pydantic v1/v2 conflicts between AG2, CrewAI, LangGraph). Independent Dockerfiles with isolated virtualenvs are the only clean solution.

```
a2a-xp/
├── agents/
│   ├── ag2/
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI + A2aAgentServer bootstrap
│   │   │   └── agent.py         # ConversableAgent definition
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── requirements.txt
│   ├── crewai/
│   │   ├── app/
│   │   │   ├── main.py          # Crew + A2AServerConfig bootstrap
│   │   │   └── crew.py          # Crew, Agent, Task definitions
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── requirements.txt
│   └── langgraph/
│       ├── app/
│       │   └── graph.py         # StateGraph definition
│       ├── langgraph.json        # Agent Server descriptor
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── requirements.txt
├── infra/
│   └── docker-compose.yml       # postgres, redis, shared network
├── client/
│   ├── main.py                  # A2A test client
│   └── requirements.txt
├── docker-compose.yml           # root: include: all sub-composes
└── openspec/
```

**Alternative considered:** flat single Docker Compose — rejected due to dependency hell and brittleness between frameworks.

### D2 — LangGraph: self-hosted via `langchain/langgraph-api` image

The `langchain/langgraph-api` Docker image is the Agent Server binary. Your graph code is mounted in at runtime via a `LANGGRAPH_DESCRIPTOR` volume. This is the documented self-hosted path for non-commercial use.

```
┌──────────────────────────────────────────────┐
│  langchain/langgraph-api (official image)     │
│  ├── embedded FastAPI + task queue            │
│  ├── reads langgraph.json descriptor          │
│  └── mounts → /deps/app/graph.py             │
│          ↕ postgres (checkpoints)             │
│          ↕ redis (task queue)                 │
└──────────────────────────────────────────────┘
```

A2A endpoint auto-generated at `/a2a/{assistant_id}`.

**Alternative considered:** wrapping LangGraph in a custom FastAPI — adds boilerplate and loses the official A2A integration; rejected for the learning lab context.

### D3 — AG2: `A2aAgentServer` + FastAgency

AG2 (autogen-agentchat ~0.5+) ships `A2aAgentServer`. FastAgency provides the ASGI runtime. Pattern:

```python
from autogen_agentchat.agents import AssistantAgent
from fastagency import A2aAgentServer

agent = AssistantAgent("rhyme-completer", ...)
app = A2aAgentServer(agent).build()   # returns FastAPI app
```

Exposed via uvicorn on port 10000.

### D4 — CrewAI: `A2AServerConfig` inline

```python
from crewai import Crew, Agent, Task
from crewai.a2a import A2AServerConfig

crew = Crew(
    agents=[...],
    tasks=[...],
    a2a=A2AServerConfig(url="http://crewai-agent:10001")
)
```

CrewAI handles AgentCard generation and HTTP routing internally. Exposed on port 10001.

### D5 — Docker port assignment

| Service         | Internal | External |
|-----------------|----------|----------|
| ag2-agent       | 8000     | 10000    |
| crewai-agent    | 8000     | 10001    |
| langgraph-agent | 8000     | 10002    |
| postgres        | 5432     | 5432     |
| redis           | 6379     | 6379     |

### D6 — Docker Compose profiles

Root `docker-compose.yml` uses profiles so each sub-project can be started selectively:

```bash
docker compose --profile ag2 up
docker compose --profile crewai up
docker compose --profile langgraph up
docker compose up   # all three
```

### D7 — Shared Docker network

All services share `a2a-net` bridge network. The test client can reach all agents by service name.

### D8 — LLM provider

OpenAI API key via `OPENAI_API_KEY` env var, injected via `.env` file at root. Each sub-project's container reads it from the environment. No LLM provider is bundled.

## Risks / Trade-offs

- **[Risk] CrewAI `A2AServerConfig` API surface may be unstable** — This feature was introduced in early 2026 and documentation is sparse. If the API changes, we fall back to wrapping CrewAI in a custom FastAPI endpoint. → Mitigation: pin CrewAI version in requirements.txt.

- **[Risk] `langchain/langgraph-api` image may require license acceptance** — The image pulls from Docker Hub and may prompt for terms on first pull for certain use cases. → Mitigation: Check image EULA before first use; for learning/non-commercial this is documented as free.

- **[Risk] pydantic v1/v2 conflicts inside containers** — AG2 and LangGraph have historically conflicted on pydantic versions. → Mitigation: isolation via separate Docker images fully isolates this.

- **[Trade-off] The demo agent is trivial** — A simple rhyme completer doesn't stress-test agent reasoning, but that's intentional. The goal is to compare A2A plumbing ergonomics, not LLM capabilities.

## Migration Plan

N/A — greenfield project. To start: `git clone` → create `.env` with `OPENAI_API_KEY` → `docker compose up`.

## Open Questions

- Does FastAgency's `A2aAgentServer` expose `/.well-known/agent.json` automatically, or does the path need configuration?
- Does CrewAI's `A2AServerConfig` support SSE streaming, or only synchronous responses?
- Which version of the AG2 package (`autogen-agentchat`, `pyautogen`, or `ag2`) is the canonical one to use in 2026?
