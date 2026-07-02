# SPECIFICATIONS

This folder contains the technical specifications, architecture notes, contracts, and seed data for the Internal Enterprise Chatbot platform. It is intended to help developers understand the system boundaries, integration requirements, data contracts, and local setup assets before implementation.

## docs/

The `docs/` folder contains the human-readable engineering documentation for the platform. These files define the system architecture, API behavior, data model, security expectations, and testing workflow.

### architecture.md

Explains the overall chatbot platform architecture, including the frontend widget, centralized backend, PostgreSQL product registry, and Qdrant vector store. It also documents request flow, authentication, product isolation, scalability, and future enhancements.

### api-specification.md

Defines the REST API surface for chat, document upload, product management, and health checks. It includes authentication requirements, request and response examples, validation rules, status codes, errors, and curl examples.

### database-schema.md

Documents the PostgreSQL schema used by the platform, especially the `internal_products` registry table. It explains columns, constraints, indexes, relationships, validation rules, JSONB usage, and SQL examples.

### project-folder-structure.md

Describes the recommended production repository layout for backend, frontend, database, Qdrant, scripts, seed data, tests, and documentation. It exists to keep implementation structure predictable across teams.

### qdrant-payload-schema.md

Defines how vector payload metadata is stored in Qdrant. It explains required fields, product-level filtering, tenant-aware payload indexing, and the isolation strategy based on `product_id`.

### request-response-contracts.md

Documents communication contracts between the frontend widget, backend API, PostgreSQL, Qdrant, and frontend responses. It standardizes required fields, validation behavior, success responses, and error contracts.

### security.md

Describes the platform security model, including internal service tokens, hashing, authentication, authorization, product isolation, secrets management, PostgreSQL security, and Qdrant security.

### seed-data.md

Explains the purpose and structure of the seed data files. It describes internal products, branding configuration, document references, Qdrant payload examples, and business-confirmation items.

### testing-guide.md

Provides a developer workflow for validating the platform locally or in a shared development environment. It covers database seeding, vector import, backend/frontend startup, authentication checks, isolation tests, and troubleshooting.

## seed/

The `seed/` folder contains structured seed data used for local development, integration testing, and implementation validation. These files provide realistic internal product records, UI themes, document references, and Qdrant metadata payloads.

### products.json

Contains internal product registry seed records, including product IDs, product names, service token hash placeholders requiring business confirmation, active status, and branding configuration. It maps directly to the PostgreSQL product registry.

### qdrant_payloads.json

Contains sample Qdrant vector payload metadata for product-scoped document chunks. It is used to validate payload structure, `product_id` isolation, citation metadata, and vector import workflows.

### sample_documents.json

Contains realistic internal document references for each product, including title, source, language, document type, content summary, owner, and classification. It supports document ingestion and retrieval testing.

### themes.json

Contains product-specific widget theme configuration such as colors, launcher labels, widget titles, and welcome messages. It helps frontend developers validate product branding behavior consistently.
