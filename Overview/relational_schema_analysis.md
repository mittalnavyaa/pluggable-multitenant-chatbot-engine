# Relational Schema Mapping & Token Verification Analysis

This report provides a detailed codebase analysis, trace flow, schema design, and implementation map for building the PostgreSQL internal product registry and token verification middleware.

---

## Relevant Files and Code Responsibilities

### 1. `docker/postgres/init.sql`
* **Relevance**: Contains the raw DDL schema definitions for PostgreSQL.
* **Responsibility**: Exposes initial SQL statements to build tables (`internal_products`, `bots`, `document_registry`, etc.), indexes, constraints, and foreign key relations.
* **Action**: Reference only (table structures are already provisioned in PostgreSQL via Docker setup).

### 2. `apps/central-hub-backend/src/database/base.py`
* **Relevance**: Core database base definition.
* **Responsibility**: Exposes `Base` (SQLAlchemy DeclarativeBase) subclass for model registrations.
* **Action**: Reference only.

### 3. `apps/central-hub-backend/src/database/database.py`
* **Relevance**: Database connection manager.
* **Responsibility**: Reads `DATABASE_URL` env variable, configures `create_engine` and the session factory `SessionLocal`.
* **Action**: Reference only.

### 4. `apps/central-hub-backend/src/models/internal_product.py`
* **Relevance**: Object Relational Mapping (ORM) model for products.
* **Responsibility**: Maps the database table `internal_products` to a Python class.
* **Action**: Modify (currently empty; needs SQLAlchemy column mappings).
* **Classes involved**: `InternalProduct` model class.

### 5. `apps/central-hub-backend/src/models/bot.py`
* **Relevance**: ORM model for bots.
* **Responsibility**: Maps database table `bots` to a Python class.
* **Action**: Reference/Modify (already maps to `bots`, could add relationship definitions if needed).
* **Classes involved**: `Bot` model class.

### 6. `apps/central-hub-backend/src/middleware/auth.py`
* **Relevance**: Request authentication layer.
* **Responsibility**: Handles incoming requests, extracts the authorization token, verifies it against stored PostgreSQL hashes, and registers the resolved `product_id`.
* **Action**: Modify (currently a placeholder/stub).
* **Functions involved**: `authenticate_request(request, call_next)`.

### 7. `apps/central-hub-backend/src/services/ingestion_service.py`
* **Relevance**: Document ingestion handler.
* **Responsibility**: Performs product/bot existence checks and inserts new database records using raw queries.
* **Action**: Reference/Modify (transition from raw SQL queries to ORM model interactions).

---

## Database Request & Authentication Trace Flow

```
Application Startup (main.py)
        ↓
Reads DATABASE_URL (src/database/database.py)
        ↓
SQLAlchemy engine & SessionLocal created
        ↓
Import models dynamically (registers tables in Base)
        ↓
FastAPI Startup Complete (Uvicorn running)
        ↓
Incoming Client Request with Token (e.g. X-Internal-Service-Token header)
        ↓
FastAPI Auth Middleware (src/middleware/auth.py)
        ↓
Hash token value (using Argon2/Bcrypt helper)
        ↓
Query internal_products table by service_token_hash (src/models/internal_product.py)
        ↓
Validate Product is active (is_active = True)
        ↓
Attach product_id to Request State: request.state.product_id
        ↓
Forward request to Upload Router
```

---

## Schema Analysis

The columns for the product registry are defined as follows:

| Column Name | SQL Data Type | ORM Class Mapper | Indexes / Constraints |
| --- | --- | --- | --- |
| `id` | `UUID` | `UUID(as_uuid=True)` | `PRIMARY KEY` (Auto-generated v4) |
| `product_id` | `VARCHAR(100)` | `String(100)` | `UNIQUE`, `NOT NULL` (Optimized keyword search) |
| `product_name` | `VARCHAR(150)` | `String(150)` | `NOT NULL` |
| `internal_service_token_hash` | `TEXT` | `String` | `NOT NULL`, Indexed for fast verification |
| `ui_theme_config` | `JSONB` | `JSONB` | Supports dynamic JSON properties |
| `created_at` | `TIMESTAMP` | `DateTime` | Default `CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP` | `DateTime` | Default `CURRENT_TIMESTAMP` |

---

## Authentication Dependency Analysis

1. **Service Token Extraction**: In `src/middleware/auth.py`, read the request headers for `X-Internal-Service-Token` or `Authorization`.
2. **Hashing**: Use a hashing helper (e.g., standard library `hashlib.sha256` or `passlib/bcrypt/argon2` if dependency is added) to compute the comparison hash.
3. **Database Query**: Query the database using the ORM session `SessionLocal`:
   ```python
   # Example Query
   product = db.execute(select(InternalProduct).filter_by(internal_service_token_hash=token_hash)).scalar_one_or_none()
   ```
4. **State Injection**: Attach the resolved product ID to the request state:
   ```python
   request.state.product_id = product.id
   ```

---

## Migration & Seed Infrastructure

* **Migration system**: Alembic is currently not configured or used in the Python backend. The database schema initialization is handled by docker startup running `docker/postgres/init.sql`.
* **Seed Scripts**: Seed data files reside in `bot/seed/`. They can be populated in Python using database execution sessions.
* **Schema Modifications**: Any new database tables should first be declared in DDL format in `docker/postgres/init.sql` and mapped inside the backend directory under `src/models/`.

---

## Existing Architecture Review

* **Organization/Tenant/Client models**: None currently exist.
* **Product Model**: `src/models/internal_product.py` is the logical model for managing tenant contexts, mapped logically through the token identification process.
* **Recommendations**: Implement the `InternalProduct` SQLAlchemy class inside `src/models/internal_product.py` to match the exact schema structure of the `internal_products` table in `init.sql`.

---

## Feature Dependency Graph

```
Application Startup
        ↓
Database Engine (database.py)
        ↓
Declarative Base (base.py)
        ↓
Internal Product ORM (internal_product.py)
        ↓
Database Session Dependency (get_db)
        ↓
Auth Middleware (auth.py)
        ↓
FastAPI HTTP Routing Lifecycle
```

---