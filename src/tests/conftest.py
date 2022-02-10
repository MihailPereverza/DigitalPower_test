import aioredis
import pytest_asyncio

from aioredis import Redis

from ..workshop.db.connection import metadata, engine
from ..workshop.settings import settings


@pytest_asyncio.fixture(autouse=True)
async def base():
    metadata.drop_all(engine)
    metadata.create_all(engine)

    try:
        yield
    finally:
        metadata.drop_all(engine)
        metadata.create_all(engine)


@pytest_asyncio.fixture
async def redis() -> Redis:
    session: Redis = await aioredis.from_url(settings.redis_url)
    await session.flushall()
    yield session
