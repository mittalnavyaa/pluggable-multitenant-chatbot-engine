import logging
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import HnswConfigDiff, VectorParams, Distance, KeywordIndexParams, KeywordIndexType, PointStruct
from uuid import uuid4
from src.init_qdrant import qdrant_client, QDRANT_COLLECTION, EMBEDDING_DIMENSION

logger = logging.getLogger("qdrant_service")
if not logger.handlers:
    import sys
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def ensure_collection_initialized():
    """
    Idempotently ensures that the shared Qdrant collection is created
    and the payload indexes for product_id and bot_id are configured.
    """
    try:
        # 1. Check if the collection already exists
        try:
            collection_info = qdrant_client.get_collection(QDRANT_COLLECTION)
            collection_exists = True
            logger.info("Collection already exists.")
        except (UnexpectedResponse, Exception):
            collection_exists = False

        # 2. If the collection does not exist, create it
        if not collection_exists:
            logger.info("Creating Qdrant collection...")
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                ),
                hnsw_config=HnswConfigDiff(
                    m=0,
                    payload_m=16
                )
            )
            logger.info("Collection created.")
            # Fetch the collection info after creation to parse payload schema
            collection_info = qdrant_client.get_collection(QDRANT_COLLECTION)

        # 3. Check and create payload indexes idempotently
        payload_schema = collection_info.payload_schema

        # product_id index
        if "product_id" in payload_schema:
            logger.info("Payload index already exists.")
        else:
            logger.info("Creating payload index...")
            qdrant_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="product_id",
                field_schema=KeywordIndexParams(
                    type=KeywordIndexType.KEYWORD,
                    is_tenant=True
                )
            )

        # bot_id index
        if "bot_id" in payload_schema:
            logger.info("Payload index already exists.")
        else:
            logger.info("Creating payload index...")
            qdrant_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="bot_id",
                field_schema=KeywordIndexParams(
                    type=KeywordIndexType.KEYWORD,
                    is_tenant=True
                )
            )

        logger.info("Qdrant initialization completed.")

    except Exception as e:
        logger.error(f"Qdrant initialization failed: {str(e)}")
        raise RuntimeError(f"Failed to initialize Qdrant vector database: {str(e)}") from e

def upsert_document_chunks(
    product_id: str,
    bot_id: str,
    document_id: str,
    source_filename: str,
    chunks: list[dict],
    embeddings: list[list[float]]
):
    """
    Upserts document chunks and their embeddings into the Qdrant collection.
    """
    points = []
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid4())
        payload = {
            "product_id": product_id,
            "bot_id": bot_id,
            "document_id": document_id,
            "chunk_id": idx,
            "page_number": chunk.get("page_number", 1),
            "source_filename": source_filename,
            "content": chunk.get("text", "")
        }
        points.append(
            PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
        )

    # Ensure collection and tenant indexes are active before upserting
    ensure_collection_initialized()

    qdrant_client.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )
    logger.info(f"Successfully upserted {len(points)} chunks to Qdrant for document {document_id}")
