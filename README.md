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
- `POST /`                        — A2A JSON-RPC endpoint (`tasks/send`)

## Comparison Notes

| Criterion                  | AG2         | CrewAI      | LangGraph    |
|----------------------------|-------------|-------------|--------------|
| A2A plumbing               | a2a-sdk     | a2a-sdk     | native       |
| Streaming (SSE)            | TBD         | TBD         | Yes          |
| State persistence          | none        | none        | postgres     |
| Docker complexity          | low         | low         | high         |
| Framework boilerplate      | TBD         | TBD         | TBD          |

> Fill in the "TBD" cells after running the end-to-end validation (task 8.4).
