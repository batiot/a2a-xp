## ADDED Requirements

### Requirement: AG2 agent exposes A2A AgentCard
The service SHALL expose a valid A2A AgentCard at `GET /.well-known/agent.json` describing the rhyme-completer skill.

#### Scenario: AgentCard discovery
- **WHEN** a client sends `GET /.well-known/agent.json` to the ag2-agent service
- **THEN** the response SHALL be HTTP 200 with a JSON body containing `name`, `description`, `skills`, and `url` fields

#### Scenario: Skill declaration
- **WHEN** the AgentCard is retrieved
- **THEN** it SHALL declare at least one skill with id `rhyme-completer` describing the 3-petits-chats task

### Requirement: AG2 agent accepts A2A tasks via JSON-RPC
The service SHALL accept `POST /` (or the A2A task endpoint) with a valid A2A JSON-RPC 2.0 payload and return a task response.

#### Scenario: Valid task submission
- **WHEN** a client POSTs a valid A2A `tasks/send` JSON-RPC payload with a text message (a partial rhyme line)
- **THEN** the service SHALL return HTTP 200 with a JSON-RPC response containing the next rhyme line as the task result

#### Scenario: Invalid payload rejected
- **WHEN** a client POSTs a malformed JSON body (not valid JSON-RPC)
- **THEN** the service SHALL return HTTP 400 or a JSON-RPC error response

### Requirement: AG2 agent built with A2aAgentServer
The agent implementation SHALL use `A2aAgentServer` from FastAgency wrapping an AG2 `AssistantAgent`, without hand-rolling the A2A HTTP plumbing.

#### Scenario: Server startup
- **WHEN** the Docker container starts
- **THEN** the uvicorn server SHALL start successfully and log that it is listening on port 8000

### Requirement: AG2 agent independently runnable via Docker
The sub-project `agents/ag2/` SHALL contain a `Dockerfile` and `docker-compose.yml` sufficient to run the agent standalone (no shared infra required).

#### Scenario: Standalone start
- **WHEN** `docker compose up` is run from `agents/ag2/`
- **THEN** the ag2-agent container SHALL start and the AgentCard endpoint SHALL be reachable at `http://localhost:10000/.well-known/agent.json`
