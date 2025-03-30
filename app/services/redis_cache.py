import os

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


async def get_cached_link(short_code: str):
    return await redis_client.get(short_code)


async def cache_link(short_code: str, original_url: str):
    await redis_client.set(short_code, original_url)


async def invalidate_cache(short_code: str):
    await redis_client.delete(short_code)


async def get_cached_link_stats(short_code: str):
    return await redis_client.get(short_code)


async def cache_link_stats(short_code: str, stats):
    await redis_client.set(short_code, stats)


async def invalidate_cache_stats(short_code: str):
    await redis_client.delete(short_code)
