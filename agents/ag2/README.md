# AG2 Agent (A2A)

## Implementation

This agent uses **AG2 v0.11.4** with its native `autogen.a2a.A2aAgentServer` to expose an `AssistantAgent` via the A2A protocol. No manual `a2a-sdk` glue is needed — AG2 handles `AgentCard` generation, `AgentExecutor` wiring, and ASGI app construction natively.

| File | Purpose |
|---|---|
| `app/agent.py` | `build_agent_server()` — builds `AssistantAgent` + `A2aAgentServer` |
| `app/main.py` | ASGI app bootstrap via `build_agent_server(url).build()` |
| `Dockerfile` | `python:3.12-slim` + `uv` + `requirements.txt` |

## Native A2A via `autogen.a2a.A2aAgentServer`

```python
from autogen import AssistantAgent
from autogen.a2a import A2aAgentServer, CardSettings

agent = AssistantAgent(
    name="rhyme_completer",
    llm_config={"config_list": [{"api_type": "google", "model": "gemini-2.0-flash-lite", "api_key": ...}]},
    human_input_mode="NEVER",
)

app = A2aAgentServer(
    agent=agent,
    url="http://ag2-agent:8000",
    agent_card=CardSettings(name="Rhyme Completer (AG2)", skills=[...]),
).build()
```

Key points:
- `ag2[a2a]` bundles `a2a-sdk[http-server]` — no separate `a2a-sdk` dep needed
- `ag2[gemini]` brings in `google-genai` for the Gemini LLM client
- LLM config: `api_type="google"` routes to Google AI Studio via `GOOGLE_STUDIO_API_KEY`
- Model: `gemini-2.0-flash-lite` (AG2's Google client, not OpenAI-compatible endpoint)
- `A2aAgentServer.build()` returns a Starlette ASGI app ready for uvicorn
- New canonical AgentCard endpoint: `/.well-known/agent-card.json` (legacy `/.well-known/agent.json` still works)

## Quick Start

```bash
cp ../../.env.example ../../.env   # add GOOGLE_STUDIO_API_KEY
docker compose up

# Verify
curl http://localhost:10000/.well-known/agent-card.json
```
