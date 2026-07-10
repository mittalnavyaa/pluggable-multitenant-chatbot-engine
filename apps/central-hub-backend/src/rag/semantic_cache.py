"""Tenant-isolated semantic Redis cache layer."""

import os
import json
import hashlib
import logging
import numpy as np
import redis
from typing import Optional, Dict, Any, List

from src.rag.retrieval_models import RuntimeResponse

logger = logging.getLogger("rag_semantic_cache")

class TenantSemanticCache:
    """Provides semantic query caching with tenant boundary guarantees."""

    def __init__(self, platform_id: str, ttl: int = 3600, similarity_threshold: float = 0.98) -> None:
        self.platform_id = platform_id.strip()
        self.ttl = ttl
        self.similarity_threshold = similarity_threshold
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.Redis.from_url(redis_url, socket_timeout=2.0)
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.redis_client = None

    def _get_query_hash(self, query: str) -> str:
        return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()

    def get(self, query: str, query_embedding: List[float]) -> Optional[RuntimeResponse]:
        """
        Scans for semantically similar queries matching the threshold.
        Returns the deserialized RuntimeResponse on a hit, otherwise None.
        """
        if not self.redis_client:
            return None

        index_pattern = f"tenant_{self.platform_id}:index:*"
        
        try:
            cursor = 0
            keys = []
            while True:
                cursor, scan_keys = self.redis_client.scan(cursor=cursor, match=index_pattern, count=100)
                keys.extend(scan_keys)
                if cursor == 0:
                    break

            if not keys:
                return None

            pipe = self.redis_client.pipeline()
            for key in keys:
                pipe.get(key)
            payloads = pipe.execute()

            best_score = -1.0
            best_response_key = None

            q_vec = np.array(query_embedding)
            norm_q = np.linalg.norm(q_vec)
            if norm_q == 0:
                return None

            for raw_payload in payloads:
                if not raw_payload:
                    continue
                try:
                    data = json.loads(raw_payload)
                    cached_vec = np.array(data["embedding"])
                    norm_c = np.linalg.norm(cached_vec)
                    if norm_c == 0:
                        continue
                    
                    similarity = float(np.dot(q_vec, cached_vec) / (norm_q * norm_c))
                    if similarity > best_score:
                        best_score = similarity
                        best_response_key = data.get("response_key")
                except Exception as ex:
                    logger.warning(f"Error parsing semantic cache index payload: {ex}")
                    continue

            if best_score >= self.similarity_threshold and best_response_key:
                logger.info(f"Semantic cache hit: similarity={best_score:.4f} for query='{query}'")
                cached_resp_data = self.redis_client.get(best_response_key)
                if cached_resp_data:
                    resp_dict = json.loads(cached_resp_data)
                    if "statistics" in resp_dict:
                        resp_dict["statistics"]["cache_hit"] = True
                    return RuntimeResponse.model_validate(resp_dict)
                    
        except Exception as e:
            logger.error(f"Redis cache lookup failed for tenant '{self.platform_id}': {e}")
            
        return None

    def set(self, query: str, query_embedding: List[float], response: RuntimeResponse) -> None:
        """
        Stores the query vector index and response payload under tenant boundaries.
        Enforces a matching TTL expiration.
        """
        if not self.redis_client:
            return

        query_hash = self._get_query_hash(query)
        index_key = f"tenant_{self.platform_id}:index:{query_hash}"
        response_key = f"tenant_{self.platform_id}:response:{query_hash}"

        try:
            index_data = {
                "query": query,
                "embedding": query_embedding,
                "response_key": response_key
            }
            
            response_copy = response.model_copy()
            response_copy.statistics.cache_hit = False
            response_json = response_copy.model_dump_json()

            pipe = self.redis_client.pipeline()
            pipe.set(index_key, json.dumps(index_data), ex=self.ttl)
            pipe.set(response_key, response_json, ex=self.ttl)
            pipe.execute()
            
            logger.info(f"Cached response stored for tenant '{self.platform_id}' (TTL: {self.ttl}s)")
            
        except Exception as e:
            logger.error(f"Failed to write query to Redis semantic cache: {e}")
