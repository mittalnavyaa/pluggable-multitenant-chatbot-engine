# Docker Workspace Environment Analysis

This report contains a comprehensive analysis and execution trace for the standardized local Docker development environment setup.

---

## Relevant Files and Code Responsibilities

### 1. `docker-compose.yml`
* **Relevance**: Core orchestration file for the localized development stack.
* **Responsibility**: Declares services (`postgres`, `qdrant`, `minio`, `redis`), handles port mapping (e.g., exposing Postgres on `5432` and Qdrant on `6333`), mounts named persistent storage volumes, and specifies execution orders and variables.
* **Action**: Reference only (can be modified if adding checks or configuring dependencies).

### 2. `docker/postgres/init.sql`
* **Relevance**: Database bootstrap initialization script.
* **Responsibility**: Contains DDL queries to set up the DB registry schema (creating tables, unique constraints, indices, extensions) immediately upon container boot.
* **Action**: Reference only.

### 3. `apps/central-hub-backend/Dockerfile`
* **Relevance**: Container build description for the FastAPI backend.
* **Responsibility**: Specifies build steps, dependencies, and entry commands for the API application.
* **Action**: Reference only (backend currently runs on the host for local development).

### 4. `.env.example`
* **Relevance**: Configuration template.
* **Responsibility**: Documents required environment variables (e.g. `QDRANT_HOST`, `QDRANT_PORT`, `POSTGRES_HOST`) to instruct developer configurations.
* **Action**: Reference only.

---

## Local Development Startup Flow

```
Developer runs docker compose up -d
        ↓
Docker engine creates bridge network & named volumes (postgres_data, qdrant_data, minio_data)
        ↓
chatbot-postgres & chatbot-qdrant containers initialized
        ↓
Postgres container maps init.sql and executes schemas on startup
        ↓
Developer copies .env.example to .env (sets localhost targets)
        ↓
FastAPI app runs locally (uvicorn src.main:app)
        ↓
Backend connects to Postgres (localhost:5432) and Qdrant (localhost:6333)
        ↓
RAG Central Hub Engine operational and ready
```

---

## Docker Compose & Container Analysis

### PostgreSQL (`chatbot-postgres`):
* **Image**: `postgres:16`
* **Port**: `5432:5432` (exposes Postgres globally to the host)
* **Environment variables**: `POSTGRES_USER=chatbot`, `POSTGRES_PASSWORD=chatbot123`, `POSTGRES_DB=chatbot_db`.
* **Initialization Volume**: `./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql`

### Qdrant (`chatbot-qdrant`):
* **Image**: `qdrant/qdrant:latest`
* **Port**: `6333:6333` (exposes Qdrant API endpoint)
* **Persistent Volume**: `qdrant_data:/qdrant/storage` (preserves collections across restarts)

### Environment Variable Injection:
* When running locally, environment configurations are loaded from a `.env` file via `python-dotenv` inside the application startup lifecycle (`src/main.py`).

---

## Container Networking Analysis

```
Host Machine (Local Dev)
   │
   ├─[localhost:5432]─────► chatbot-postgres (Port 5432)
   │
   ├─[localhost:6333]─────► chatbot-qdrant (Port 6333)
   │
   └─[localhost:6379]─────► chatbot-redis (Port 6379)
```

Inside the Docker Compose bridge network, containers communicate directly using their service name hostnames (e.g. `postgres:5432` or `qdrant:6333`).

---

## Feature Dependency Graph

```
Developer
      ↓
docker compose up -d
      ↓
Docker Network / Volumes
      ↓
Postgres (init.sql executed) & Qdrant Containers Up
      ↓
Environment Configuration (.env loaded)
      ↓
FastAPI backend (startup hooks)
      ↓
Application Operational
```

---