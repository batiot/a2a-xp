## ADDED Requirements

### Requirement: CrewAI agent exposes A2A AgentCard
The service SHALL expose a valid A2A AgentCard at `GET /.well-known/agent.json` describing the rhyme-completer skill.

#### Scenario: AgentCard discovery
- **WHEN** a client sends `GET /.well-known/agent.json` to the crewai-agent service
- **THEN** the response SHALL be HTTP 200 with a JSON body containing `name`, `description`, `skills`, and `url` fields

#### Scenario: Skill declaration
- **WHEN** the AgentCard is retrieved
- **THEN** it SHALL declare at least one skill with id `rhyme-completer`

### Requirement: CrewAI agent accepts A2A tasks via JSON-RPC
The service SHALL accept A2A `tasks/send` requests and return the next rhyme line as the task result.

#### Scenario: Valid task submission
- **WHEN** a client POSTs a valid A2A `tasks/send` JSON-RPC payload with a partial rhyme line
- **THEN** the service SHALL invoke the CrewAI Crew and return the next line of "3 petits chats" as the result

#### Scenario: Invalid payload rejected
- **WHEN** a client POSTs a malformed JSON body
- **THEN** the service SHALL return HTTP 400 or a JSON-RPC error response

### Requirement: CrewAI agent configured with A2AServerConfig
The agent implementation SHALL use `A2AServerConfig` from `crewai.a2a` to declare the A2A server URL on the `Crew` object, without hand-rolling the HTTP plumbing.

#### Scenario: A2A config present
- **WHEN** the Crew is instantiated
- **THEN** the `a2a` parameter SHALL be set to an `A2AServerConfig` instance with the service URL

### Requirement: CrewAI agent independently runnable via Docker
The sub-project `agents/crewai/` SHALL contain a `Dockerfile` and `docker-compose.yml` sufficient to run the agent standalone.

#### Scenario: Standalone start
- **WHEN** `docker compose up` is run from `agents/crewai/`
- **THEN** the crewai-agent container SHALL start and the AgentCard endpoint SHALL be reachable at `http://localhost:10001/.well-known/agent.json`
