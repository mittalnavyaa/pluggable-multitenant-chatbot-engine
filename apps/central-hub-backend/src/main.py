from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.middleware.auth import authenticate_request
from src.routers.upload import router as upload_router
from src.routers.bots import router as bots_router
from src.routers.products import router as products_router
from src.routers.dashboard import router as dashboard_router
from src.services.storage_service import initialize_bucket
from src.services.qdrant_service import ensure_collection_initialized

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(authenticate_request)

app.include_router(upload_router)
app.include_router(bots_router)
app.include_router(products_router)
app.include_router(dashboard_router)

@app.on_event("startup")
def startup():
    initialize_bucket()
    ensure_collection_initialized()

    # Run dynamic schema migrations on startup to clean up local postgres schemas
    from sqlalchemy import text
    from src.database.database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("""
            DO $$
            BEGIN
                -- 1. Drop old global unique constraint on document_hash if it exists
                IF EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'document_registry_document_hash_key'
                ) THEN
                    ALTER TABLE document_registry DROP CONSTRAINT document_registry_document_hash_key;
                END IF;

                -- 2. Add composite unique constraint if not exists
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'unique_bot_document_hash'
                ) THEN
                    ALTER TABLE document_registry ADD CONSTRAINT unique_bot_document_hash UNIQUE (bot_id, document_hash);
                END IF;

                -- 3. Add bots.product_id foreign key constraint if not exists
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'bots_product_id_fkey'
                ) THEN
                    ALTER TABLE bots ADD CONSTRAINT bots_product_id_fkey FOREIGN KEY (product_id) REFERENCES internal_products(id) ON DELETE CASCADE;
                END IF;
            END $$;
        """))
        db.commit()
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger("uvicorn").error(f"Error running database schema updates on startup: {e}")
    finally:
        db.close()

@app.get("/")
def root():

    return {

        "message": "Central Hub Backend Running"

    }

