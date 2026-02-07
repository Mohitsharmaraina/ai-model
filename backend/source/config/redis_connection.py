import redis.asyncio as redis
from redis.cluster import RedisCluster
from config_secrets import settings

async def get_redis_client():
    """
    Returns a Redis or RedisCluster client based on configuration.
    This effectively abstracts the infrastructure change.
    """
    connection_kwargs = {
        "host": settings.redis_host,
        "port": settings.redis_port,
        "password": settings.redis_password,
        "decode_responses": True, # Important for reading text back
    }

    if settings.REDIS_SSL:
        connection_kwargs["ssl"] = True

    if settings.REDIS_CLUSTER_MODE:
        # AWS ElastiCache Cluster
        return RedisCluster(**connection_kwargs)
    else:
        # Local Redis Stack
        return redis.Redis(**connection_kwargs)