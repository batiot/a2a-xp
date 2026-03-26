## 1. LangGraph — Replace LangGraph Server with a2a-sdk ASGI Server

- [x] 1.1 Add `a2a-sdk[http-server]==0.3.25` and `uvicorn[standard]==0.42.0` to `agents/langgraph/requirements.txt`; pin `langgraph` and `langchain-*` to exact versions
- [x] 1.2 Create `agents/langgraph/app/agent_executor.py` wrapping the compiled `graph` in an `AgentExecutor` that calls `graph.ainvoke()` with a `HumanMessage` and enqueues the result
- [x] 1.3 Create `agents/langgraph/app/main.py` bootstrapping `A2AStarletteApplication` with an `AgentCard` for "Rhyme Completer (LangGraph)", port 8000, URL from `AGENT_URL` env var
- [x] 1.4 Update `agents/langgraph/Dockerfile`: change `FROM langchain/langgraph-api:python3.12` to `FROM python:3.12-slim`; add `pip install uv && uv pip install --system --no-cache -r requirements.txt`; change CMD to `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [x] 1.5 Update `agents/langgraph/docker-compose.yml`: remove `depends_on: [postgres, redis]`; remove infra include if present
- [x] 1.6 Update root `docker-compose.yml`: LangGraph profile no longer needs infra services; remove `infra/docker-compose.yml` include
- [x] 1.7 Run `agents/langgraph/` tests — 14/14 passed (including new `test_app.py`)

## 2. CrewAI — Audit Native A2A and Simplify or Document

- [x] 2.1 Probe `crewai==1.11.1`: `crewai.a2a` exists with `A2AServerConfig`, `A2AClientConfig`, `inject_a2a_server_methods`
- [x] 2.2 Update `agents/crewai/app/crew.py`: add `A2AServerConfig` to rhyme-expert Agent; add `inject_a2a_server_methods`; expose `get_agent_card(url)` function
- [x] 2.3 Update `agents/crewai/app/main.py`: use `get_agent_card(AGENT_URL)` from CrewAI instead of manually constructing `AgentCard`; keep `a2a-sdk` for HTTP transport (CrewAI provides no built-in ASGI server)
- [x] 2.4 Run `agents/crewai/` tests — 9/9 passed

## 3. AG2 — Audit Native A2A and Document

- [x] 3.1 Probe `autogen-agentchat==0.7.5`: no native A2A server primitive found (added in v0.10, not yet available at pinned version)
- [x] 3.2 Keep existing `a2a-sdk` pattern unchanged (current implementation is already idiomatic and tested)
- [x] 3.3 Add `agents/ag2/README.md` documenting audit findings and rationale for keeping current version
- [x] 3.4 Run `agents/ag2/` tests — 9/9 passed
