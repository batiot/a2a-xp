## 1. LangGraph — Replace LangGraph Server with a2a-sdk ASGI Server

- [ ] 1.1 Add `a2a-sdk[http-server]==0.3.25` and `uvicorn[standard]==0.42.0` to `agents/langgraph/requirements.txt`; pin `langgraph` and `langchain-*` to exact versions
- [ ] 1.2 Create `agents/langgraph/app/agent_executor.py` wrapping the compiled `graph` in an `AgentExecutor` that calls `graph.ainvoke()` with a `HumanMessage` and enqueues the result
- [ ] 1.3 Create `agents/langgraph/app/main.py` bootstrapping `A2AStarletteApplication` with an `AgentCard` for "Rhyme Completer (LangGraph)", port 8000, URL from `AGENT_URL` env var
- [ ] 1.4 Update `agents/langgraph/Dockerfile`: change `FROM langchain/langgraph-api:python3.12` to `FROM python:3.12-slim`; add `pip install uv && uv pip install --system --no-cache -r requirements.txt`; change CMD to `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [ ] 1.5 Update `agents/langgraph/docker-compose.yml`: remove `depends_on: [postgres, redis]`; remove infra include if present
- [ ] 1.6 Update root `docker-compose.yml`: LangGraph profile should no longer include infra services
- [ ] 1.7 Run `agents/langgraph/` tests to verify the new ASGI server passes existing test suite

## 2. CrewAI — Audit Native A2A and Simplify or Document

- [ ] 2.1 Probe the installed `crewai==1.11.1` package: check for `crewai.a2a` module and `A2AServerConfig` / `A2AClientConfig` availability
- [ ] 2.2 **If native `crewai.a2a` is available**: replace `agent_executor.py` + `a2a-sdk` with `A2AServerConfig`; update `requirements.txt` to remove `a2a-sdk`; update `main.py`
- [ ] 2.3 **If not available**: keep existing code unchanged; add `agents/crewai/README.md` documenting findings (what was checked, what version would be needed, link to CrewAI roadmap if known)
- [ ] 2.4 Run `agents/crewai/` tests to confirm no regression

## 3. AG2 — Audit Native A2A and Document

- [ ] 3.1 Probe `autogen-agentchat==0.7.5`: check for any native A2A server primitive (e.g. `A2aAgentServer`, `a2a` submodule, or equivalent)
- [ ] 3.2 **If native A2A available in 0.7.5**: migrate `agents/ag2/app/agent.py` to use it; remove `a2a-sdk` from `agents/ag2/requirements.txt`
- [ ] 3.3 **If not available**: add `agents/ag2/README.md` documenting findings; no code change (current `a2a-sdk` pattern is already idiomatic)
- [ ] 3.4 Run `agents/ag2/` tests to confirm no regression
