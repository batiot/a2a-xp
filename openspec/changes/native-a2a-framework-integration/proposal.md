## Why

The initial `a2a-multiframework-lab` used `a2a-sdk` as a uniform A2A wrapper for all three frameworks. This approach works, but misses the opportunity to exercise each framework's dedicated A2A integration path. The goal of this change is to replace the generic wrappers with the most native approach available for each framework:

- **CrewAI** ships a native A2A module (`crewai.a2a`) with `A2AServerConfig` that handles AgentCard generation and HTTP routing internally — no manual `a2a-sdk` glue needed.
- **LangGraph** should run *without* the `langchain/langgraph-api` heavy server image. Instead, wrap the compiled `StateGraph` in a lightweight `a2a-sdk` ASGI server — eliminating the postgres + redis infrastructure dependency for this sub-project.
- **AG2** already uses a native a2a-sdk pattern that is clean enough. We verify whether the native AG2 v0.10 `A2aAgentServer` support (if available in the pinned version) can replace the hand-wired `AgentExecutor` approach.

## What Changes

- **agents/crewai/**: Replace `a2a-sdk` `AgentExecutor` wrapper with `crewai.a2a.A2AServerConfig`, letting CrewAI own the server runtime natively.
- **agents/langgraph/**: Drop the `langchain/langgraph-api` Docker image. Add `a2a-sdk[http-server]` and a custom `main.py` + `agent_executor.py` that wraps the compiled `StateGraph`. Remove postgres + redis infra dependency.
- **agents/ag2/**: Audit native AG2 A2A support. If `autogen-agentchat>=0.10` introduces a dedicated A2A server API, migrate to it; otherwise keep the current clean `a2a-sdk` pattern and document why no change is needed.

## Capabilities

### Modified Capabilities

- `crewai-a2a-agent`: Now uses `crewai.a2a.A2AServerConfig` natively; removes `a2a-sdk` dependency from `agents/crewai/`.
- `langgraph-a2a-agent`: Now runs as a lightweight ASGI process (python:3.12-slim + uvicorn + a2a-sdk) instead of the heavy `langchain/langgraph-api` image. No longer requires postgres or redis.
- `ag2-a2a-agent`: Either migrated to native AG2 A2A (v0.10+) or kept as-is with a documented rationale.

### New Capabilities

- None — this change improves internals, not external protocol behaviour.

## Impact

- `agents/crewai/requirements.txt`: remove `a2a-sdk`, rely on `crewai[a2a]` or equivalent.
- `agents/crewai/app/`: remove `agent_executor.py`; simplify `main.py` to use `A2AServerConfig`.
- `agents/langgraph/Dockerfile`: FROM `python:3.12-slim` (was `langchain/langgraph-api:python3.12`).
- `agents/langgraph/requirements.txt`: add `a2a-sdk[http-server]`, `uvicorn[standard]`.
- `agents/langgraph/app/`: add `main.py` and `agent_executor.py`.
- `agents/langgraph/docker-compose.yml`: remove `depends_on: postgres, redis`.
- Root `docker-compose.yml`: LangGraph profile no longer needs infra services.
- No change to A2A protocol behaviour visible to the test client.
