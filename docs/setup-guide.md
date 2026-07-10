# Setup Guide

Complete guide for setting up the Envoy pluggable multi-tenant chatbot engine
for local development.

---

## Repository Structure

```
pluggable-multitenant-chatbot-engine/
├── packages/
│   ├── chatbot-ui/              @envoy/chatbot-ui — Frontend Web Component widget
│   ├── chatbot-backend-sdk/     @envoy/chatbot-backend-sdk — Node.js proxy SDK
│   ├── shared-contracts/        @envoy/shared-contracts — Shared types and validation
│   └── security/                @envoy/security — HMAC signing and verification
├── apps/
│   └── central-hub-backend/     Core FastAPI RAG engine
├── dashboard/                   Internal admin dashboard (React/Vite)
├── ai-mock-integration/         Developer onboarding and mock integration environment
├── docker/                      Docker configuration files
├── docker-compose.yml           Full infrastructure stack
└── docs/                        Project-level documentation
```

---

## Prerequisites

| Tool | Version | Purpose |
| :--- | :--- | :--- |
| Node.js | 18+ | Widget, SDK, dashboard |
| pnpm | 8+ | Monorepo package manager |
| Python | 3.11+ | Core backend, FastAPI mock server |
| Docker Desktop | Latest | PostgreSQL, Qdrant, Redis, MinIO |

---

## Quick Start — Mock Integration (No Docker)

The fastest way to see the platform working locally.

```bash
# 1. Install Node packages
pnpm install

# 2. Build the widget
cd packages/chatbot-ui && pnpm build

# 3. Build the SDK
cd packages/chatbot-backend-sdk && npm run build

# 4. Start the mock Express server
cd ai-mock-integration/express-server
npm install
cp .env.example .env
npm start

# 5. Open the demo
# http://localhost:3000
```

---

## Full Stack Setup (With Docker)

### Step 1 — Start infrastructure

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port 5432
- Qdrant on port 6333
- Redis on port 6379
- MinIO on ports 9000/9001
- Core FastAPI backend on port 8000
- Celery worker

### Step 2 — Verify services

```bash
# PostgreSQL
docker exec -it chatbot-postgres psql -U chatbot -d chatbot_db -c "\dt"

# Qdrant dashboard
open http://localhost:6333/dashboard

# Core backend
curl http://localhost:8000/
```

### Step 3 — Build frontend packages

```bash
pnpm install
cd packages/chatbot-ui && pnpm build
cd packages/chatbot-backend-sdk && npm run build
```

### Step 4 — Start the host server

```bash
cd ai-mock-integration/express-server
cp .env.example .env
# Edit .env: set CHATBOT_API_BASE=http://localhost:8000
npm start
```

### Step 5 — Open the demo

```
http://localhost:3000
```

---

## Admin Dashboard

```bash
cd dashboard
pnpm install
pnpm dev
# http://localhost:5173
```

---

## Document Processing Pipeline

```bash
cd bot/document-processing
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your LLM provider credentials

# Run the pipeline on a sample document
python examples/run_pipeline.py
```

---

## Environment Variables Reference

| File | Purpose |
| :--- | :--- |
| `.env.example` (root) | PostgreSQL and Qdrant connection settings |
| `ai-mock-integration/express-server/.env.example` | Express mock server configuration |
| `ai-mock-integration/fastapi-server/.env.example` | FastAPI mock server configuration |
| `bot/document-processing/.env.example` | Document processing pipeline configuration |
| `dashboard/.env.example` | Dashboard frontend configuration |

---

## Ports Reference

| Service | Port | URL |
| :--- | :--- | :--- |
| Mock Express server | 3000 | http://localhost:3000 |
| Mock FastAPI server | 8001 | http://localhost:8001 |
| Core FastAPI backend | 8000 | http://localhost:8000 |
| Admin dashboard | 5173 | http://localhost:5173 |
| PostgreSQL | 5432 | — |
| Qdrant | 6333 | http://localhost:6333/dashboard |
| Redis | 6379 | — |
| MinIO | 9000/9001 | http://localhost:9001 |

---

## Further Reading

- [Installation Guide](../ai-mock-integration/docs/installation.md)
- [Configuration Guide](../ai-mock-integration/docs/configuration.md)
- [Integration Flow](../ai-mock-integration/integration/integration-flow.md)
- [Testing Guide](../ai-mock-integration/docs/testing.md)
- [Troubleshooting](../ai-mock-integration/docs/troubleshooting.md)
- [API Contracts](api-contracts.md)
- [Architecture](architecture.md)
