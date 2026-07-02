# Project Folder Structure

## Recommended Repository Layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── services/
│   │   └── config/
│   ├── tests/
│   └── README.md
├── frontend/
│   ├── widget/
│   │   ├── src/
│   │   ├── public/
│   │   └── package.json
│   └── README.md
├── database/
│   ├── migrations/
│   ├── schema.sql
│   └── README.md
├── qdrant/
│   ├── collection-config.json
│   ├── payload-indexes.json
│   └── README.md
├── scripts/
│   ├── seed-database.*
│   ├── import-vectors.*
│   └── verify-isolation.*
├── seed/
│   ├── products.json
│   ├── themes.json
│   ├── sample_documents.json
│   └── sample_payloads.json
├── tests/
│   ├── integration/
│   ├── contract/
│   └── security/
├── docs/
│   ├── architecture.md
│   ├── api-specification.md
│   ├── database-schema.md
│   ├── qdrant-payload-schema.md
│   ├── request-response-contracts.md
│   ├── security.md
│   ├── seed-data.md
│   ├── testing-guide.md
│   └── project-folder-structure.md
└── README.md
```

## Folder Responsibilities

| Folder | Purpose |
| --- | --- |
| `backend/` | Central chatbot backend API, authentication, orchestration, retrieval, and ingestion |
| `backend/app/api/` | REST endpoint handlers and request validation |
| `backend/app/auth/` | Token hashing, product resolution, and authorization utilities |
| `backend/app/ingestion/` | Document chunking, embedding generation, and Qdrant upserts |
| `backend/app/retrieval/` | Product-scoped vector search and citation assembly |
| `backend/app/services/` | Shared service clients for PostgreSQL, Qdrant, and model providers |
| `frontend/` | Embeddable chat widget and product integration assets |
| `frontend/widget/src/` | Widget UI components, API client, state management, and theme handling |
| `database/` | PostgreSQL schema, migrations, and database documentation |
| `qdrant/` | Qdrant collection configuration, payload index configuration, and import notes |
| `scripts/` | Developer and CI utilities for seeding, import, verification, and maintenance |
| `seed/` | Enterprise seed data for local development and integration testing |
| `tests/` | Cross-component integration, contract, and security tests |
| `docs/` | Architecture, API, schema, security, and operational documentation |

## Naming Standards

| Asset | Convention | Example |
| --- | --- | --- |
| Product IDs | Lowercase kebab case | `internal-support` |
| Document IDs | Prefix with `doc_` | `doc_hr_leave_policy` |
| Conversation IDs | Prefix with `conv_` | `conv_01HZX9Y7A6P2` |
| Message IDs | Prefix with `msg_` | `msg_01HZX9Z2J8N5` |
| Request IDs | Prefix with `req_` | `req_01HZX8R2J3C4VT` |

## Development Principles

| Principle | Application |
| --- | --- |
| Product context is server-owned | Resolve `product_id` from token, never request body |
| Retrieval is scoped by default | Query builders must require product filters |
| Documentation lives with code | API, schema, and security docs are versioned in repository |
| Seed data is realistic but safe | Seed values must not contain real secrets or employee data |
