from __future__ import annotations

import os
import uvicorn

from app.agent import build_agent_server

# Fail fast on missing API key
_GOOGLE_STUDIO_API_KEY = os.environ["GOOGLE_STUDIO_API_KEY"]

AGENT_URL = os.environ.get("AGENT_URL", "http://ag2-agent:8000")

# The native AG2 A2aAgentServer handles AgentCard generation, AgentExecutor
# wiring, and A2AStarletteApplication construction — no manual plumbing needed.
app = build_agent_server(AGENT_URL).build()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
