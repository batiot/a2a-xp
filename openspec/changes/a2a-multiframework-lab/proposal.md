## Why

This project is a self-hosted, open-source learning lab to compare how three major Python agent frameworks — AG2 (AutoGen + FastAgency), CrewAI, and LangGraph — each implement the A2A (Agent-to-Agent) protocol. There is no single reference showing these three side-by-side with the same demo agent, and the differences in plumbing, memory, and Docker packaging are non-trivial.

## What Changes

- Introduce a monorepo with three independent sub-projects (`agents/ag2/`, `agents/crewai/`, `agents/langgraph/`) each exposing the same demo agent via A2A
- Add shared infra (`infra/`) for postgres + redis, consumed mostly by LangGraph Agent Server
- Add a minimal A2A test client (`client/`) that validates AgentCard discovery and task execution against all three agents
- Add a root `docker-compose.yml` that orchestrates all three agents + shared infra as optional profiles
- Demo agent for all three sub-parts: a French children's rhyme completer — given the first line(s) of "3 petits chats", the agent returns the next line(s) (simple, deterministic enough to compare outputs, fun)

## Capabilities

### New Capabilities

- `ag2-a2a-agent`: AG2 ConversableAgent wrapped with `A2aAgentServer`, exposed via FastAgency + uvicorn, self-contained Docker service
- `crewai-a2a-agent`: CrewAI Crew with `A2AServerConfig`, exposing an A2A endpoint, self-contained Docker service
- `langgraph-a2a-agent`: LangGraph StateGraph deployed on the self-hosted Agent Server (`langchain/langgraph-api` image), backed by postgres + redis
- `a2a-test-client`: Lightweight Python client that calls `/.well-known/agent.json` and sends A2A tasks to all three agents, validating protocol compliance
- `docker-infra`: Shared Docker Compose infrastructure (postgres, redis, shared network, profiles)

### Modified Capabilities

## Impact

- New top-level folders: `agents/`, `infra/`, `client/`
- Each agent sub-project is independently runnable via its own `docker-compose.yml`
- Root `docker-compose.yml` uses `include:` to compose all three + infra
- Python dependencies are isolated per container (no shared virtualenv)
- Non-commercial use — `langchain/langgraph-api` official image is acceptable
- No existing code modified (greenfield project)
