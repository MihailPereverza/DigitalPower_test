import random
import pytest

from asynctest import patch as async_patch, CoroutineMock
from fastapi.testclient import TestClient
from mock import Mock
from aioredis import Redis

from ..workshop.app import app
from ..workshop.models.auth import UserCreate
from ..workshop.constants import EMOTICON_POSTFIX
from ..workshop.constants import UNAUTHORIZED_MESSAGE


emoticons = {
    'oehosa': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x14\x00\x00\x00\x14\x08\x06\x00\x00\x00\x8d\x89\x1d\r\x00\x00\x00\x06bKGD\x00\xff\x00\xff\x00\xff\xa0\xbd\xa7\x93\x00\x00\x00nIDAT8\x8dc`\x18\x05\x94\x02FB\n\xb6\xc4\x85\xfeG\xe6\xfb,Z\x8dW\x0f^It\xc3\x885\x94 \xd8\x12\x17\xfa\x1f\x97\xe1\xe8\x80\xea^f"\xc6\x10R\xd4`5\x90\xea\x00f;6W\xe0\x93c````\xc1g\xa8\xcf\xa2\xd5\x8c\xd8\xc2\x10_\x90\xe0\x0c`B\xe1\x88+r0\x04\x89M\x1e\x84\x0c\xc60\x10\x9f\xc1\xf8\xd4P=\xd9\x8c\x02\xca\x01\x00\x1fZ@\nt\xdd\xac=\x00\x00\x00\x00IEND\xaeB`\x82'   # noqa
}


def side_effect_emoticon(url):
    values = {f'http://emoticon:8080/monster/{key}': emoticons[key]
              for key in emoticons.keys()}

    if values.get(url):
        res = Mock()
        res.read = CoroutineMock(return_value=values.get(url))
        res.status = 200
        return res
    raise RuntimeError('Incorrect url')


def set_emoticon_response_mock(mock_get: CoroutineMock,
                               status: int):
    mock_get.side_effect = side_effect_emoticon
    mock_get.status = status


@pytest.fixture
def user_data() -> UserCreate:
    return UserCreate(username=random.choice(list(emoticons.keys())),
                      password='andrey1h98#')


@pytest.mark.asyncio
async def test_get_emoticon_with_auth(user_data: UserCreate, redis: Redis):
    username = user_data.username
    user_emoticon = emoticons[username]

    with async_patch(target="aiohttp.ClientSession.get",
                     new=CoroutineMock()) as mocked_get:
        set_emoticon_response_mock(mocked_get, 200)

        with TestClient(app) as client:
            response = client.post('/auth/sign-up', json=user_data.dict())
            response_data = response.json()
            access_token = response_data['access_token']

            login_headers = {'Authorization': f'Bearer {access_token}'}
            response = client.get(url='/emoticon',
                                  headers=login_headers,
                                  params={'username': username})

            response_data = response.content

        assert response_data == user_emoticon
        assert response.status_code == 200
        assert await redis.get(username + EMOTICON_POSTFIX) == user_emoticon


@pytest.mark.asyncio
async def test_get_emoticon_without_auth(user_data: UserCreate, redis: Redis):
    with async_patch("aiohttp.ClientSession.get", new=CoroutineMock()) as mocked_get:  # noqa
        set_emoticon_response_mock(mocked_get, 200)

        with TestClient(app) as client:
            client.post('/auth/sign-up', json=user_data.dict())

            response = client.get(url='/emoticon',
                                  params={'username': user_data.username})

    assert response.status_code == 401
    assert response.json() == {'detail': UNAUTHORIZED_MESSAGE}


@pytest.mark.asyncio
async def test_get_emoticon_from_cache(user_data: UserCreate, redis: Redis):
    username = user_data.username
    user_emoticon = emoticons[username]
    await redis.set(username + EMOTICON_POSTFIX, user_emoticon)

    with async_patch("aiohttp.ClientSession.get", new=CoroutineMock()) as mocked_get:   # noqa
        set_emoticon_response_mock(mocked_get, 200)

        with TestClient(app) as client:
            response = client.post('/auth/sign-up', json=user_data.dict())
            response_data = response.json()
            access_token = response_data['access_token']

            login_headers = {'Authorization': f'Bearer {access_token}'}
            response = client.get(url='/emoticon/',
                                  headers=login_headers,
                                  params={'username': username})

            response_data = response.content

    mocked_get.assert_not_called()

    assert response_data == user_emoticon
    assert response.status_code == 200
    assert await redis.get(username + EMOTICON_POSTFIX) == user_emoticon
