## 0. GitHub Copilot Instructions

- [x] 0.1 Create `.github/copilot-instructions.md` as the root instructions file for GitHub Copilot
- [x] 0.2 Add project context section: monorepo with 3 independent Python agent sub-projects (AG2, CrewAI, LangGraph), each in `agents/<name>/`; shared infra in `infra/`; test client in `client/`
- [x] 0.3 Add Python tooling rule: always use `uv` for dependency management and virtual environments (`uv venv`, `uv pip install`, `uv run`); never use bare `pip` or `python -m venv`
- [x] 0.4 Add tool-use guidance section: use `mcp_context7_resolve-library-id` + `mcp_context7_get-library-docs` for up-to-date library docs (AG2, CrewAI, LangGraph, FastAgency, a2a-python); use `mcp_cognitionai_d_read_wiki_contents` (DeepWiki) for in-depth codebase understanding; use `mcp_perplexity_perplexity_search` for recent news, release notes, or when docs are unclear
- [x] 0.5 Add testing rules section: always run tests after implementing any feature; for each agent sub-project run `uv run pytest` before marking the task done; prefer testing observable behaviour (A2A endpoint responses) over internal implementation details; test edge cases (missing env vars, malformed payloads) alongside the happy path
- [x] 0.6 Add code quality rules: follow the testing strategy from the image (behaviour not implementation, 3-question rule, pyramid: many unit → fewer integration → minimal E2E); no dead code or unused imports; pin all dependency versions in `requirements.txt`
- [x] 0.7 Add A2A-specific guidance: always validate `/.well-known/agent.json` response shape before calling `tasks/send`; use `httpx` (async-capable) for all HTTP calls in the test client; log A2A task IDs for traceability

## 1. Repository Skeleton

- [x] 1.1 Create top-level folder structure: `agents/ag2/`, `agents/crewai/`, `agents/langgraph/`, `infra/`, `client/`
- [x] 1.2 Create root `.env.example` with `OPENAI_API_KEY=` placeholder
- [x] 1.3 Create root `.gitignore` covering `.env`, `__pycache__`, `.venv`, `*.pyc`
- [x] 1.4 Create root `README.md` documenting the project structure and quick-start

## 2. Shared Docker Infrastructure (`infra/`)

- [x] 2.1 Create `infra/docker-compose.yml` defining `postgres` service (image: `postgres:16`, env: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`)
- [x] 2.2 Add `redis` service to `infra/docker-compose.yml` (image: `redis:7-alpine`)
- [x] 2.3 Declare shared external network `a2a-net` in `infra/docker-compose.yml`
- [x] 2.4 Add named volumes for postgres data persistence

## 3. AG2 + FastAgency Agent (`agents/ag2/`)

- [x] 3.1 Create `agents/ag2/requirements.txt` pinning `autogen-agentchat`, `fastagency`, `uvicorn`
- [x] 3.2 Create `agents/ag2/app/agent.py` defining an AG2 `AssistantAgent` with a system prompt for the rhyme-completer task
- [x] 3.3 Create `agents/ag2/app/main.py` bootstrapping `A2AStarletteApplication` with `RhymeCompleterExecutor` and returning the ASGI app
- [x] 3.4 Create `agents/ag2/Dockerfile` (FROM python:3.12-slim, install requirements, CMD uvicorn)
- [x] 3.5 Create `agents/ag2/docker-compose.yml` exposing port 10000→8000, network `a2a-net`, env `OPENAI_API_KEY`
- [ ] 3.6 Test standalone: `docker compose up` from `agents/ag2/` and verify `GET http://localhost:10000/.well-known/agent.json` returns 200

## 4. CrewAI Agent (`agents/crewai/`)

- [x] 4.1 Create `agents/crewai/requirements.txt` pinning `crewai` + `a2a-sdk`, `uvicorn`
- [x] 4.2 Create `agents/crewai/app/crew.py` defining the `Agent`, `Task`, and `Crew`
- [x] 4.3 Create `agents/crewai/app/agent_executor.py` wrapping Crew in an A2A `AgentExecutor`
- [x] 4.3 Create `agents/crewai/app/main.py` bootstrapping `A2AStarletteApplication`
- [x] 4.4 Create `agents/crewai/Dockerfile` (FROM python:3.12-slim, install requirements)
- [x] 4.5 Create `agents/crewai/docker-compose.yml` exposing port 10001→8000, network `a2a-net`, env `OPENAI_API_KEY`
- [ ] 4.6 Test standalone: `docker compose up` from `agents/crewai/` and verify `GET http://localhost:10001/.well-known/agent.json` returns 200

## 5. LangGraph Agent Server (`agents/langgraph/`)

- [x] 5.1 Create `agents/langgraph/requirements.txt` pinning `langgraph`, `langchain-core`, `langchain-openai`
- [x] 5.2 Create `agents/langgraph/app/graph.py` defining a `StateGraph` with `messages` state and a single LLM node for rhyme completion
- [x] 5.3 Create `agents/langgraph/langgraph.json` descriptor pointing to the compiled graph (`app/graph.py:graph`)
- [x] 5.4 Create `agents/langgraph/Dockerfile` (FROM `langchain/langgraph-api:python3.12`, mount app code)
- [x] 5.5 Create `agents/langgraph/docker-compose.yml` with `depends_on: postgres, redis`, exposes port 10002→8000, network `a2a-net`, env `OPENAI_API_KEY`, `LANGSMITH_API_KEY` (optional, can be blank)
- [ ] 5.6 Test standalone: `docker compose -f infra/docker-compose.yml -f agents/langgraph/docker-compose.yml up` and verify `GET http://localhost:10002/.well-known/agent.json` returns 200

## 6. A2A Test Client (`client/`)

- [x] 6.1 Create `client/requirements.txt` pinning `httpx`, `rich` (for pretty output)
- [x] 6.2 Create `client/main.py` that: (1) queries `/.well-known/agent.json` for each agent, (2) sends the same `tasks/send` A2A payload to each, (3) prints responses side-by-side using `rich`
- [x] 6.3 Parametrize agent URLs via environment variables (`AG2_URL`, `CREWAI_URL`, `LANGGRAPH_URL`) with defaults pointing to Docker service names
- [x] 6.4 Create `client/Dockerfile` (FROM python:3.12-slim, install requirements, CMD python main.py)

## 7. Root Docker Compose Orchestration

- [x] 7.1 Create root `docker-compose.yml` using `include:` to reference `infra/docker-compose.yml`, `agents/ag2/docker-compose.yml`, `agents/crewai/docker-compose.yml`, `agents/langgraph/docker-compose.yml`
- [x] 7.2 Add `client` service to root `docker-compose.yml` (build from `client/`, network `a2a-net`, `profiles: [client]`)
- [x] 7.3 Add `profiles` to each agent service: `ag2`, `crewai`, `langgraph`
- [x] 7.4 Document profile usage in `README.md`: `docker compose --profile ag2 up`, etc.

## 8. End-to-End Validation

- [ ] 8.1 Start all services from root: `docker compose up`
- [ ] 8.2 Run test client: `docker compose run client` and verify all three AgentCards are printed
- [ ] 8.3 Verify all three agents return the next line of "3 petits chats" for the same input prompt
- [ ] 8.4 Document findings (ergonomics, streaming support, memory, quirks) in `README.md` under a "Comparison Notes" section
