# GitHub Copilot Instructions — a2a-xp

## Project Context

This is a **learning lab monorepo** comparing three Python agent frameworks
([AG2/autogen-agentchat](https://github.com/ag2ai/ag2),
[CrewAI](https://github.com/crewaiinc/crewai),
[LangGraph Agent Server](https://github.com/langchain-ai/langgraph)) each
implementing the same agent exposed via the A2A (Agent-to-Agent) protocol.

```
a2a-xp/
├── agents/
│   ├── ag2/          ← AG2 + a2a-sdk (A2AStarletteApplication)
│   ├── crewai/       ← CrewAI + a2a-sdk (A2AStarletteApplication)
│   └── langgraph/    ← LangGraph StateGraph + langchain/langgraph-api image
├── infra/            ← postgres + redis (LangGraph only)
├── client/           ← A2A test client (validates all 3 agents)
└── .github/
```

Each `agents/<name>/` sub-project is **independently runnable** via its own
`docker-compose.yml`. The root `docker-compose.yml` composes all three using
`include:` and Docker profiles (`--profile ag2`, `--profile crewai`,
`--profile langgraph`).

**Demo agent task for all three:** Complete the French children's rhyme
"3 petits chats" — given a partial verse, return the next one.

**LLM provider:** Google AI Studio (Gemini). Key: `GOOGLE_STUDIO_API_KEY`.
Model: `gemini-3.1-flash-lite-preview` across all three agents.

**A2A plumbing (AG2 & CrewAI):** `a2a-sdk` (`A2AStarletteApplication`,
`AgentExecutor`, `DefaultRequestHandler`, `InMemoryTaskStore`).

**A2A plumbing (LangGraph):** Built-in to `langchain/langgraph-api` image.

---

## Python Tooling — Always Use `uv`

**Never use bare `pip` or `python -m venv`.** Always use `uv`:

```bash
# Create virtual environment (local dev)
uv venv && source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run scripts and tools
uv run pytest
uv run uvicorn app.main:app --reload

# Add a dependency (then update requirements.txt with pinned version)
uv pip install <package>
uv pip freeze | grep <package>   # grab the pinned version for requirements.txt
```

In Dockerfiles, install `uv` and use it system-wide:

```dockerfile
RUN pip install uv && uv pip install --system --no-cache -r requirements.txt
```

---

## Tool-Use Guidance

Use the right tool before writing framework-specific code.

### For library documentation

**Always use context7** for up-to-date, version-accurate docs:

```
1. mcp_context7_resolve-library-id   → find library ID
2. mcp_context7_get-library-docs     → fetch docs with a focused topic query
```

Use this for: `autogen-agentchat`, `crewai`, `langgraph`, `a2a-sdk`,
`fastagency`, `httpx`, `langchain-core`, `langchain-openai`.

**Before writing any framework API call**, resolve it with context7.
Do not assume imports or method signatures from memory.

### For in-depth codebase understanding

Use **DeepWiki** (`mcp_cognitionai_d_read_wiki_contents`) when you need to
understand framework internals:
- How `A2AStarletteApplication` routes JSON-RPC requests
- How LangGraph checkpointing works with the Agent Server
- How `AssistantAgent` processes multi-turn conversations in AG2

### For recent news, release notes, or when docs are unclear

Use **Perplexity** (`mcp_perplexity_perplexity_search`) for:
- "does crewai support A2A in version X?"
- latest breaking changes in a package
- community workarounds for known issues
- when context7 and DeepWiki don't give a clear answer

---

## Testing Rules

**Always run tests after implementing any feature. Never mark a task done
without running the relevant tests.**

```bash
# In any agent sub-project (run from the sub-project directory)
cd agents/<name>
uv run pytest -v

# For the test client
cd client
uv run pytest -v
```

### What to test

- **Behaviour, not implementation**: test what a caller observes over HTTP
  (status codes, JSON shape, A2A response structure) — not internal function
  calls or mock assertions
- **Happy path + edge cases** for every feature:
  - Happy path: valid A2A `tasks/send` returns the next verse
  - Edge case: missing `OPENAI_API_KEY` → container fails with clear error
  - Edge case: malformed JSON payload → HTTP 400 or JSON-RPC error response
  - Edge case: agent service unreachable (in client tests)

### The 3-question rule before writing a test

1. **What bug does this test detect?** (if you can't answer → don't write it)
2. **Will it break if I refactor without changing behaviour?** (yes = bad test)
3. **Will it break if I introduce a bug in the logic?** (no = bad test)

### Test pyramid

```
         /\
        /E2E\        ← minimal (full docker-compose stack)
       /──────\
      /integr.\      ← fewer (spin up the agent, call HTTP endpoints)
     /──────────\
    /unit tests  \   ← many (fast, mocked, validate parsing + logic)
   /______________\
```

---

## Code Quality Rules

- **No dead code or unused imports** — remove them immediately
- **Pin all dependency versions** in `requirements.txt` using `==`
  (e.g., `httpx==0.28.1`). Use `uv pip freeze` after install to get exact versions.
- **No bare `except:`** — always catch specific exceptions (`except httpx.HTTPError:`)
- **Type hints on all function signatures** — use `from __future__ import annotations` at module top
- **One responsibility per file**:
  - `agent.py` or `crew.py` — framework agent/crew definition only
  - `agent_executor.py` — A2A `AgentExecutor` wrapper
  - `main.py` — server bootstrap (AgentCard + A2AStarletteApplication)
- **Env vars via `os.environ`** with explicit `KeyError` on missing required vars

---

## A2A Protocol Guidance

When implementing or calling A2A endpoints:

### Server-side (agents)

All AG2 and CrewAI agents use the `a2a-sdk` server pattern:

```python
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from a2a.utils.message import new_agent_text_message

class MyExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Extract user text from the incoming A2A message
        user_text = context.get_user_input()  # or parse context.message.parts
        result = await self._run_agent(user_text)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("cancel not supported")
```

> **Note**: The exact import paths for `a2a-sdk` may vary between versions.
> Always verify with context7 (`mcp_context7_get-library-docs` for `a2a-sdk`)
> before writing import statements.

### Client-side

```python
import httpx

# 1. Always validate AgentCard before calling tasks/send
resp = httpx.get(f"{base_url}/.well-known/agent.json", timeout=5)
assert resp.status_code == 200, f"AgentCard not found at {base_url}"
card = resp.json()
assert "skills" in card, "AgentCard missing 'skills'"

# 2. Log A2A task IDs for traceability
import logging
logger = logging.getLogger(__name__)
response = send_task(base_url, payload)
task_id = response.get("result", {}).get("id")
logger.info("A2A task submitted", extra={"task_id": task_id})

# 3. Validate response shape before accessing result
if response.get("result", {}).get("status", {}).get("state") == "failed":
    raise RuntimeError(f"Agent task failed: {response}")
```

### Port assignment

| Agent           | Internal | External |
|-----------------|----------|----------|
| ag2-agent       | 8000     | 10000    |
| crewai-agent    | 8000     | 10001    |
| langgraph-agent | 8000     | 10002    |
| postgres        | 5432     | 5432     |
| redis           | 6379     | 6379     |
