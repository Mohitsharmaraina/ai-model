import json
import numpy as np
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from config.redis_connection import get_redis_client

class SemanticCache:
    def __init__(self, index_name="semantic_cache_idx", vector_dim=1536):
        self.r = get_redis_client()
        self.index_name = index_name
        self.vector_dim = vector_dim
        self._create_index_if_not_exists()

    def _create_index_if_not_exists(self):
        """Creates the vector search index if it doesn't exist."""
        try:
            self.r.ft(self.index_name).info()
        except:
            # Schema: We store the 'response' text and the 'vector'
            schema = (
                TextField("response"), # The LLM answer
                VectorField(
                    "vector",
                    "HNSW", # Algorithm (FLAT or HNSW)
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.vector_dim,
                        "DISTANCE_METRIC": "COSINE",
                    },
                ),
            )
            definition = IndexDefinition(prefix=["cache:"], index_type=IndexType.HASH)
            self.r.ft(self.index_name).create_index(schema, definition=definition)
            print(f"Index {self.index_name} created.")

    async def check_cache(self, vector_embedding: list[float], threshold: float = 0.1):
        """
        Search for a similar query. 
        Threshold: 0.1 distance means 0.9 similarity (Cosine).
        """
        # Convert list to numpy bytes for Redis
        vector_bytes = np.array(vector_embedding, dtype=np.float32).tobytes()

        # Query syntax for KNN (K-Nearest Neighbors)
        q = (
            Query(f"(*)=>[KNN 1 @vector $vec AS score]")
            .sort_by("score")
            .return_fields("response", "score")
            .dialect(2)
        )
        
        params = {"vec": vector_bytes}
        results = self.r.ft(self.index_name).search(q, query_params=params)

        if results.docs:
            doc = results.docs[0]
            score = float(doc.score)
            
            # Check if it meets your similarity threshold
            if score <= threshold:
                return doc.response
        
        return None

    async def store_cache(self, vector_embedding: list[float], response_text: str, ttl: int = 86400):
        """Stores the embedding and response with a TTL (default 1 day)."""
        vector_bytes = np.array(vector_embedding, dtype=np.float32).tobytes()
        
        # Unique key for the cache entry
        # Ideally, hash the text prompt to make a key, or use a UUID
        import uuid
        key = f"cache:{uuid.uuid4()}"

        mapping = {
            "vector": vector_bytes,
            "response": response_text
        }
        
        # Store Hash
        self.r.hset(key, mapping=mapping)
        # Set Expiry (TTL) - automatic cleanup!
        self.r.expire(key, ttl)