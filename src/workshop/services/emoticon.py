import io
import logging

from aiohttp import ClientSession, ClientConnectorError
from aioredis import Redis
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi import status

from ..redis.connection import get_session as get_redis_session
from ..constants import EMOTICON_SERVICE
from ..constants import EMOTICON_POSTFIX


class EmoticonService:
    _postfix = EMOTICON_POSTFIX

    @classmethod
    def create_response(cls, image: bytes) -> StreamingResponse:
        output = io.BytesIO(image)
        return StreamingResponse(output, media_type='image/png')

    @classmethod
    async def generate_emoticon(cls, username: str) -> bytes:
        async with ClientSession() as session:
            response = await session.get(f'{EMOTICON_SERVICE}/{username}')
            emoticon_bytes = await response.read()
            return emoticon_bytes

    @classmethod
    async def validate_data(cls, token_username: str, url_username: str):
        exception = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Incorrect username',
            headers={
                'WWW-Authenticate': 'Bearer',
            },
        )

        if token_username != url_username:
            raise exception

    def __init__(self, redis: Redis = Depends(get_redis_session)):      # noqa
        self.redis = redis
        self.logger = logging.getLogger('main.emoticon_services')

    async def get_cache_image(self, username: str) -> bytes:
        cache = await self.redis.get(username + self._postfix)

        return cache

    async def save_image_to_redis(self, image: bytes, username: str) -> None:
        await self.redis.set(username + self._postfix, image)

    async def get_user_emoticon(self, username: str) -> StreamingResponse:
        exception = HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail='Service is not accessed',
            headers={
                'WWW-Authenticate': 'Bearer',
            },
        )

        image: bytes = await self.get_cache_image(username)
        if image is None:
            try:
                image = await self.generate_emoticon(username)
            except ClientConnectorError:
                raise exception
            await self.save_image_to_redis(image, username)

        return self.create_response(image)
