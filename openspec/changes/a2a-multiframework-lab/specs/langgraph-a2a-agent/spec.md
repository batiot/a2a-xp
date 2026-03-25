## ADDED Requirements

### Requirement: LangGraph agent exposes A2A AgentCard
The service SHALL expose a valid A2A AgentCard via the Agent Server's auto-generated A2A endpoint.

#### Scenario: AgentCard discovery
- **WHEN** a client sends `GET /.well-known/agent.json` to the langgraph-agent service
- **THEN** the response SHALL be HTTP 200 with a JSON body containing `name`, `description`, `skills`, and `url` fields

#### Scenario: A2A endpoint presence
- **WHEN** the Agent Server is running
- **THEN** the path `/a2a/{assistant_id}` SHALL be available for task submission

### Requirement: LangGraph agent accepts A2A tasks
The service SHALL accept A2A `tasks/send` requests and return the next rhyme line.

#### Scenario: Valid task submission
- **WHEN** a client POSTs a valid A2A `tasks/send` JSON-RPC payload with a partial rhyme line
- **THEN** the Agent Server SHALL invoke the LangGraph StateGraph and return the next line as the task result

#### Scenario: Streaming support
- **WHEN** a client subscribes to task updates via SSE
- **THEN** the Agent Server SHALL push intermediate state events followed by a final completion event

### Requirement: LangGraph graph defined as StateGraph with messages state
The graph SHALL be implemented as a `StateGraph` with a `messages` key in state, compatible with the Agent Server's A2A integration layer.

#### Scenario: Graph compiles
- **WHEN** `graph.py` is imported by the Agent Server
- **THEN** the compiled graph SHALL be registered as an assistant without errors

### Requirement: LangGraph agent deployed via official Agent Server image
The sub-project `agents/langgraph/` SHALL use the official `langchain/langgraph-api` Docker image as the execution runtime and mount the graph code via volume.

#### Scenario: Container starts with graph mounted
- **WHEN** `docker compose up` is run from `agents/langgraph/` (with postgres and redis available)
- **THEN** the langgraph-agent container SHALL start and serve on port 10002

### Requirement: LangGraph agent requires postgres and redis
The LangGraph Agent Server SHALL connect to postgres (for checkpoints) and redis (for task queue) at startup.

#### Scenario: Infrastructure dependency
- **WHEN** the langgraph-agent container starts without postgres and redis
- **THEN** the container SHALL fail to start and log a connection error (not silently degrade)
