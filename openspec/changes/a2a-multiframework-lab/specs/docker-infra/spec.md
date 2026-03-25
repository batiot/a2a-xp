## ADDED Requirements

### Requirement: Shared Docker network for all services
All containers (agents, infra, client) SHALL be connected to a shared bridge network named `a2a-net` so they can resolve each other by service name.

#### Scenario: Service-name resolution
- **WHEN** the test client container sends a request to `http://ag2-agent:8000`
- **THEN** Docker DNS SHALL resolve the service name to the ag2-agent container IP

### Requirement: Postgres and Redis services defined in infra
The `infra/docker-compose.yml` SHALL define `postgres` and `redis` services used by the LangGraph Agent Server.

#### Scenario: Postgres available
- **WHEN** the infra Compose stack starts
- **THEN** postgres SHALL be reachable at `postgres:5432` on the `a2a-net` network with the configured database credentials

#### Scenario: Redis available
- **WHEN** the infra Compose stack starts
- **THEN** redis SHALL be reachable at `redis:6379` on the `a2a-net` network

### Requirement: Root docker-compose.yml composes all sub-projects
The root `docker-compose.yml` SHALL use `include:` to reference all sub-project and infra Compose files, enabling `docker compose up` to start the entire lab from the repository root.

#### Scenario: Full lab start
- **WHEN** `docker compose up` is run from the repository root
- **THEN** all agent services, infra services, and the test client SHALL be started

#### Scenario: Profile-based selective start
- **WHEN** `docker compose --profile ag2 up` is run
- **THEN** only the ag2-agent container (and any required infra) SHALL start

### Requirement: Environment variables via .env file
All services SHALL read the `OPENAI_API_KEY` from a `.env` file at the repository root, following Docker Compose default env file resolution.

#### Scenario: API key injected
- **WHEN** a `.env` file containing `OPENAI_API_KEY=<value>` exists at root
- **THEN** each agent container SHALL have the `OPENAI_API_KEY` environment variable available at runtime

#### Scenario: Missing .env warning
- **WHEN** no `.env` file exists
- **THEN** docker compose SHALL warn that the variable is unset (not silently pass empty value)
