import redis.asyncio as redis
import json
from typing import Optional, Any
from pydantic import BaseModel

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)


async def redis_healthcheck() -> None:
    # TODO: Add await
    # Currently can't use await with ping() as it causes Type Error
    # An issue for this was opened on Redis GitHub already
    if redis_client.ping():
        await redis_client.aclose()
        return
    raise Exception("Redis connection not established.")


async def cache_get(key: str):
    try:
        if not await redis_client.exists(key):
            return None

        result = await redis_client.get(name=key)
    except Exception as e:
        raise Exception(f"Redis Get Failed: {e}")

    return json.loads(result)


async def cache_set(key: str, value: Any, expire_at: Optional[int] = None, expire_in: Optional[int] = None) -> None:
    try:
        if await redis_client.exists(key):
            return

        if isinstance(value, BaseModel):
            value = value.model_dump()

        await redis_client.set(key, json.dumps(value))
        if expire_at is not None:
            await redis_client.expireat(name=key, when=expire_at)

        if expire_in is not None:
            await redis_client.expire(name=key, time=expire_in)
    except Exception as e:
        raise Exception(f"Redis Set Failed: {e}")
