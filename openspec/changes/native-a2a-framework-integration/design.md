## Context

Existing monorepo at `a2a-xp/`. Three agent sub-projects already work end-to-end with `a2a-sdk` as the uniform A2A shim. This change targets the internals of each sub-project while keeping external A2A protocol behaviour identical (same AgentCard shape, same `tasks/send` → `tasks/get` flow, same ports).

## Goals / Non-Goals

**Goals:**
- CrewAI sub-project uses its own native A2A server primitive instead of `a2a-sdk`.
- LangGraph sub-project runs on a lightweight custom ASGI server (no `langchain/langgraph-api` image, no postgres/redis).
- AG2 sub-project is audited for native A2A; either upgraded or documented as already best-practice.
- No regression in the shared test client (`client/`).

**Non-Goals:**
- Changing the demo agent task (rhyme completer stays).
- Adding new A2A features (streaming, multi-turn, push notifications).
- Modifying the infra/ folder (postgres + redis remain available for other uses).
- Changing Docker port assignments.

## Decisions

### D1 — LangGraph: a2a-sdk ASGI server (same pattern as AG2/CrewAI was)

The `langchain/langgraph-api` image bundles a full task-queue server (postgres checkpointing, redis queuing). For a learning lab that only needs synchronous request/response, this is heavy and introduces mandatory infra dependencies.

**Chosen approach:** Build a `main.py` + `agent_executor.py` identical in structure to the AG2 sub-project. The `agent_executor.py` invokes the compiled LangGraph `StateGraph` synchronously inside an `async` method (using `asyncio.to_thread` or direct `async` LangGraph invocation).

```
agents/langgraph/
├── app/
│   ├── __init__.py
│   ├── graph.py          # existing StateGraph (unchanged)
│   ├── agent_executor.py # NEW: wraps graph in AgentExecutor
│   └── main.py           # NEW: A2AStarletteApplication bootstrap
├── Dockerfile             # CHANGED: FROM python:3.12-slim
├── docker-compose.yml     # CHANGED: remove depends_on postgres/redis
└── requirements.txt       # CHANGED: add a2a-sdk, uvicorn; pin langgraph
```

**Alternative rejected:** Keep `langchain/langgraph-api` but use the built-in A2A endpoint. This forces postgres+redis and ties the sub-project to LangGraph's proprietary server binary — contrary to the goal of exploring manual A2A integration.

### D2 — CrewAI: native `crewai.a2a` module

CrewAI ≥ 1.0 ships a `crewai.a2a` submodule. Inspection of the installed package determines whether `A2AServerConfig` is available. Two scenarios:

**Scenario A — `crewai.a2a` is available (preferred):**
Use `A2AServerConfig` to configure the Crew as an A2A server. CrewAI internally builds the AgentCard and ASGI app.

```python
# app/main.py
from crewai.a2a import A2AServerConfig
crew = build_crew_with_a2a_config()
app = crew.a2a_server()  # or equivalent API
```

Remove `a2a-sdk` from `requirements.txt`. Remove `agent_executor.py`.

**Scenario B — `crewai.a2a` not available in 1.11.1:**
Keep the existing `a2a-sdk` `AgentExecutor` pattern. Document the limitation and pin the version where native support was confirmed absent. No code change; document the finding in `agents/crewai/README.md`.

The implementation step will probe the installed package and choose accordingly.

### D3 — AG2: audit, then decide

Check whether `autogen-agentchat` at the pinned version exposes any native A2A server primitive beyond what `a2a-sdk` wraps. Two outcomes:

**Outcome A — native A2A available:** Migrate to it and remove `a2a-sdk`.
**Outcome B — no native A2A at current version:** Keep the existing clean `a2a-sdk` `AgentExecutor` approach, which is already idiomatic. Document findings.

### D4 — LangGraph graph invocation in AgentExecutor

LangGraph's `graph.ainvoke()` (async) is the preferred entry point. Since `a2a-sdk`'s `AgentExecutor.execute()` is already `async`, no thread pool is needed:

```python
async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
    user_text = context.get_user_input()
    from langchain_core.messages import HumanMessage
    result = await graph.ainvoke({"messages": [HumanMessage(content=user_text)]})
    last_msg = result["messages"][-1]
    await event_queue.enqueue_event(new_agent_text_message(last_msg.content))
```

### D5 — LangGraph Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install uv && uv pip install --system --no-cache -r requirements.txt
COPY app/ ./app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`langchain.json` is no longer needed at runtime (it was for the Agent Server binary).

### D6 — LangGraph docker-compose changes

Remove `depends_on: [postgres, redis]` from `agents/langgraph/docker-compose.yml`. The LangGraph sub-project becomes fully self-contained again.

The root `docker-compose.yml` LangGraph profile no longer needs to include `infra/docker-compose.yml`.

## Risks / Trade-offs

- **[Risk] `crewai.a2a` API is undocumented or unstable in 1.11.1** — Mitigated by probing the package at implementation time and falling back to the existing `a2a-sdk` pattern if necessary.
- **[Risk] LangGraph `graph.ainvoke()` may behave differently without the Agent Server runtime** — The `StateGraph` is deterministic (single rhyme-node graph); direct invocation is safe.
- **[Trade-off] Losing LangGraph checkpointing** — Removing postgres means no persistent conversation history. Acceptable for a stateless rhyme-completer demo.
