# AG2 Agent (A2A)

## Implementation

This agent wraps an AG2 `AssistantAgent` in an `a2a-sdk` `AgentExecutor` to expose it via the A2A protocol.

| File | Purpose |
|---|---|
| `app/agent.py` | `RhymeCompleterExecutor` — AG2 AssistantAgent + A2A AgentExecutor |
| `app/main.py` | `A2AStarletteApplication` bootstrap (AgentCard + ASGI app) |
| `Dockerfile` | `python:3.12-slim` + `uv` + `requirements.txt` |

## Native A2A Audit (`autogen-agentchat==0.7.5`)

**Finding: no native A2A server primitive in this version.**

Checked `autogen-agentchat==0.7.5` (and bundled `autogen-ext`) for any of:
- `A2aAgentServer`, `A2AServer`, or equivalent ASGI app factory
- A dedicated `a2a` submodule

None were found. The AG2 changelog notes that native A2A server support was added
in **v0.10** (released late 2025). At v0.7.5, the idiomatic approach is the
`a2a-sdk` `AgentExecutor` wrapper used here.

**Why no version upgrade?**
Upgrading to v0.10+ would require verifying API compatibility for `AssistantAgent`,
`OpenAIChatCompletionClient`, and task result handling — a separate change. The current
implementation is clean, tested, and fully A2A-compliant; upgrading when v0.10+ is
pinned and tested is tracked as future work.

## Quick Start

```bash
# Standalone
cp ../../.env.example ../../.env   # add GOOGLE_STUDIO_API_KEY
docker compose up

# Verify
curl http://localhost:10000/.well-known/agent.json
```
