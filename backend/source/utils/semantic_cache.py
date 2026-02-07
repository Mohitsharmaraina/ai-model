import numpy as np
import uuid
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from source.config.redis_connection import get_redis_client


class SemanticCache:
    def __init__(self,redis_client, index_name="semantic_cache_idx", vector_dim=384):
        self.r = redis_client
        self.index_name = index_name
        self.vector_dim = vector_dim
      

    async def _create_index_if_not_exists(self):
        """Creates the vector search index if it doesn't exist."""
        try:
            await self.r.ft(self.index_name).info()
        except:
            print(f"Creating index {self.index_name}...")
            # Schema: We store the 'response' text and the 'vector'
            schema = (
                TextField("turn_id"), # the id of the user chat turn
                TextField("session_id"), # the id of the chat session
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
            await self.r.ft(self.index_name).create_index(schema, definition=definition)
            print(f"Index {self.index_name} created.")

    async def check_cache(self, vector_embedding: list[float], threshold: float = 0.1):
        print("Checking cache for similar query...")
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
           .return_fields("turn_id", "session_id", "score")
            .dialect(2)
        )
        
        params = {"vec": vector_bytes}
        results =await self.r.ft(self.index_name).search(q, query_params=params)

        if results.docs:
            doc = results.docs[0]
            score = float(doc.score)
            
            # Check if it meets your similarity threshold
            if score <= threshold:
                print(f"Cache Hit! Score: {score}")
                return {
                    "turn_id": doc.turn_id,
                    "session_id": doc.session_id # Ensure your Schema uses 'session_id' (fixed typo)
                }
            print(f"Cache miss: score {score} exceeds threshold {threshold}")
        
        return None

    async def store_cache(self, vector_embedding: list[float], turn_id: str, session_id: str, ttl: int = 86400):
        print("Storing cache entry...")
        """Stores the embedding and response with a TTL (default 1 day)."""
        vector_bytes = np.array(vector_embedding, dtype=np.float32).tobytes()
        
        # Unique key for the cache entry
        # Ideally, hash the text prompt to make a key, or use a UUID
       
        key = f"cache:{turn_id}"

        mapping = {
            "vector": vector_bytes,
            "turn_id": turn_id,
            "session_id": session_id,
        }
        
        try:
            await self.r.hset(key, mapping=mapping)
            await self.r.expire(key, ttl)
            print(f"Cache entry stored with key {key}.")
        except Exception as e:
            print(f"Error storing cache entry: {e}")