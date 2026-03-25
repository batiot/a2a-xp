## ADDED Requirements

### Requirement: Test client discovers all three AgentCards
The test client SHALL query `/.well-known/agent.json` on each of the three agent services and print the card contents.

#### Scenario: All three cards discovered
- **WHEN** the test client is run with all three agents running
- **THEN** it SHALL print the AgentCard JSON for ag2-agent, crewai-agent, and langgraph-agent in sequence

#### Scenario: Agent unreachable
- **WHEN** one or more agent services are not running
- **THEN** the test client SHALL print an error for the unavailable agent(s) and continue with the remaining ones

### Requirement: Test client sends same rhyme prompt to all three agents
The test client SHALL send an identical A2A `tasks/send` request — a partial line from "3 petits chats" — to each agent and collect the responses.

#### Scenario: Rhyme prompt sent
- **WHEN** the test client is run
- **THEN** it SHALL send the input text `"3 petits chats / qui mangeaient des rats"` to each available agent

#### Scenario: Side-by-side response display
- **WHEN** all three agents respond
- **THEN** the test client SHALL print the responses from each agent side-by-side or in labeled blocks for easy comparison

### Requirement: Test client runs as a Docker container
The `client/` directory SHALL contain a `Dockerfile` and be included in the root `docker-compose.yml` so the test client can run containerized on the `a2a-net` network.

#### Scenario: Client container execution
- **WHEN** `docker compose run client` is executed
- **THEN** the test client container SHALL connect to the agent services by Docker service name and output results to stdout
