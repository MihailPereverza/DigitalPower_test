import aioredis

from ..settings import settings


async def get_session() -> aioredis.Redis:
    session = await aioredis.from_url(settings.redis_url)
    yield session
