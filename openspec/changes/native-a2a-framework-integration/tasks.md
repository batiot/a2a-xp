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

## 3. AG2 — Upgrade to ag2==0.11.4 and Use Native A2aAgentServer

- [x] 3.1 Replace `autogen-agentchat==0.7.5` + `autogen-ext[openai]==0.7.5` + `a2a-sdk` with `ag2[a2a,gemini]==0.11.4` in `agents/ag2/requirements.txt`
- [x] 3.2 Rewrite `agents/ag2/app/agent.py`: use `autogen.AssistantAgent` with `llm_config` dict (`api_type: google`) + expose `build_agent_server(url)` returning native `A2aAgentServer`
- [x] 3.3 Simplify `agents/ag2/app/main.py`: single line `app = build_agent_server(AGENT_URL).build()` — no manual `AgentCard`/`AgentExecutor`/`A2AStarletteApplication`
- [x] 3.4 Update `agents/ag2/tests/test_app.py`: replace `RhymeCompleterExecutor` unit test with `test_native_server_builds_and_serves_agent_card` that validates `/.well-known/agent-card.json`
- [x] 3.5 Update `agents/ag2/README.md` with native A2A usage guide
- [x] 3.6 Run `agents/ag2/` tests — 9/9 passed
