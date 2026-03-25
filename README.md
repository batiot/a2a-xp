# a2a-xp — A2A Protocol Learning Lab

A monorepo comparing three Python agent frameworks, each implementing the same
demo agent exposed via the [A2A (Agent-to-Agent) protocol](https://a2a-protocol.org/).

## Frameworks compared

| Sub-project          | Framework         | A2A plumbing             | Port  |
|----------------------|-------------------|--------------------------|-------|
| `agents/ag2/`        | AG2 (autogen)     | `a2a-sdk` + Starlette    | 10000 |
| `agents/crewai/`     | CrewAI            | `a2a-sdk` + Starlette    | 10001 |
| `agents/langgraph/`  | LangGraph         | `langchain/langgraph-api`| 10002 |

**Demo task:** Given a partial French children's rhyme ("3 petits chats /
qui mangeaient des rats"), return the next line.

## Structure

```
a2a-xp/
├── agents/
│   ├── ag2/          ← AG2 agent + docker-compose.yml (standalone)
│   ├── crewai/       ← CrewAI agent + docker-compose.yml (standalone)
│   └── langgraph/    ← LangGraph agent + docker-compose.yml (needs infra)
├── infra/            ← postgres + redis (for LangGraph)
├── client/           ← A2A test client
├── docker-compose.yml  ← root: composes everything with profiles
└── .github/
    └── copilot-instructions.md
```

## Quick Start

### Prerequisites

- Docker + Docker Compose v2.20+
- OpenAI API key

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in OPENAI_API_KEY
```

### 2. Run a single agent (standalone)

Each sub-project is independently runnable:

```bash
# AG2 agent only
cd agents/ag2
docker compose up

# CrewAI agent only
cd agents/crewai
docker compose up

# LangGraph agent (needs infra running first)
cd /path/to/repo
docker compose -f infra/docker-compose.yml -f agents/langgraph/docker-compose.yml up
```

### 3. Run everything from root

```bash
# All agents + infra
docker compose up

# Specific agent only (using profiles)
docker compose --profile ag2 up
docker compose --profile crewai up
docker compose --profile langgraph up
```

### 4. Run the test client

```bash
# With all agents running:
docker compose run client
```

## Local development

Uses `uv` for Python dependency management:

```bash
cd agents/ag2          # (or crewai, langgraph, client)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
uv run uvicorn app.main:app --reload --port 8000
```

## A2A Endpoints

Once running, each agent exposes:

- `GET  /.well-known/agent.json` — AgentCard discovery
- `POST /`                        — A2A JSON-RPC endpoint (`message/send`)

## Running Tests

Each sub-project has a `tests/` directory. Run with `uv run pytest` from the
sub-project directory (no Docker, no real API key required — LLM is mocked):

```bash
cd agents/ag2    && uv run pytest
cd agents/crewai && uv run pytest
cd agents/langgraph && uv run pytest
cd client        && uv run pytest
```

## Comparison Notes

| Criterion                  | AG2                     | CrewAI                  | LangGraph             |
|----------------------------|-------------------------|-------------------------|-----------------------|
| A2A plumbing               | `a2a-sdk` + Starlette   | `a2a-sdk` + Starlette   | `langchain/langgraph-api` image |
| A2A method                 | `message/send`          | `message/send`          | Native (via image)    |
| Streaming (SSE)            | No (synchronous)        | No (synchronous)        | Yes (built-in)        |
| State persistence          | None (in-memory)        | None (in-memory)        | Postgres checkpoints  |
| Docker complexity          | Low                     | Low                     | High (postgres+redis) |
| Framework boilerplate      | AgentExecutor wrapper   | AgentExecutor wrapper   | Graph descriptor only |
| LLM integration            | OpenAI-compat endpoint  | LiteLLM (`gemini/` prefix) | `langchain-google-genai` |
| Sync / async               | Native async            | Sync (thread-pooled)    | Sync node, async graph |
| Dependency isolation       | Per-image venv          | Per-image venv          | Per-image venv        |

**Key findings:**
- AG2 and CrewAI share the same `a2a-sdk` plumbing pattern — almost identical
  server bootstrap code. Difference is purely in the agent/crew definition.
- CrewAI's `kickoff()` is synchronous and must be dispatched via
  `asyncio.get_running_loop().run_in_executor()` to avoid blocking uvicorn.
- LangGraph has the richest A2A feature set out-of-the-box (streaming, push
  notifications, task history) but requires postgres + redis, making standalone
  development more complex.
- All three expose `/.well-known/agent.json` automatically via their respective
  A2A plumbing — no hand-rolling of the AgentCard HTTP endpoint needed.
- The `a2a-sdk` version 0.3.x uses `message/send` (not the older `tasks/send`);
  always verify the method name against the installed SDK version.
