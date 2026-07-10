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

def ensure_collection_initialized(client=None):
    """
    Idempotently ensures that the shared Qdrant collection is created
    and the payload indexes for product_id and bot_id are configured.
    """
    db_client = client or qdrant_client
    try:
        # 1. Check if the collection already exists
        try:
            collection_info = db_client.get_collection(QDRANT_COLLECTION)
            collection_exists = True
            logger.info("Collection already exists.")
        except (UnexpectedResponse, Exception):
            collection_exists = False

        # 2. If the collection does not exist, create it
        if not collection_exists:
            logger.info("Creating Qdrant collection...")
            db_client.create_collection(
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
            collection_info = db_client.get_collection(QDRANT_COLLECTION)

        # 3. Check and create payload indexes idempotently
        payload_schema = collection_info.payload_schema

        # product_id index
        if "product_id" in payload_schema:
            logger.info("Payload index already exists.")
        else:
            logger.info("Creating payload index...")
            db_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="product_id",
                field_schema=KeywordIndexParams(
                    type=KeywordIndexType.KEYWORD,
                    is_tenant=True
                )
            )

        # platform_id index
        if "platform_id" in payload_schema:
            logger.info("Platform_id payload index already exists.")
        else:
            logger.info("Creating platform_id payload index...")
            db_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="platform_id",
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
            db_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="bot_id",
                field_schema=KeywordIndexParams(
                    type=KeywordIndexType.KEYWORD,
                    is_tenant=True
                )
            )

        # element_type index
        if "element_type" in payload_schema:
            logger.info("Element_type payload index already exists.")
        else:
            logger.info("Creating element_type payload index...")
            db_client.create_payload_index(
                collection_name=QDRANT_COLLECTION,
                field_name="element_type",
                field_schema=KeywordIndexParams(
                    type=KeywordIndexType.KEYWORD
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
    import uuid
    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_{idx}"))
        chunk_metadata = chunk.get("metadata", {})
        payload = {
            "product_id": product_id,
            "platform_id": product_id,
            "bot_id": bot_id,
            "document_id": document_id,
            "chunk_id": idx,
            "page_number": chunk_metadata.get("page_number", chunk.get("page_number", 1)),
            "page_start": chunk_metadata.get("page_start", chunk.get("page_number", 1)),
            "page_end": chunk_metadata.get("page_end", chunk.get("page_number", 1)),
            "element_type": chunk_metadata.get("element_type", "paragraph"),
            "heading_path": chunk_metadata.get("heading_path", ""),
            "parent_headings": chunk_metadata.get("parent_headings", {}),
            "section_title": chunk_metadata.get("section_title", "Root"),
            "source_filename": source_filename,
            "content": chunk.get("text", ""),
            "token_count": chunk_metadata.get("token_count"),
            "character_count": chunk_metadata.get("character_count"),
            "chunk_index": chunk_metadata.get("chunk_index", idx)
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
