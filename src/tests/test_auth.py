import pytest
import pytest_asyncio

from fastapi.testclient import TestClient
from jose import jwt
from passlib.handlers.bcrypt import bcrypt
from typing import List, Iterable

from ..workshop.app import app
from ..workshop.settings import settings
from ..workshop.db.User import User as DBUser
from ..workshop.db.connection import database
from ..workshop.constants import INCORRECT_USERNAME_OR_PASS_MESSAGE
from ..workshop.constants import INCORRECT_TOKEN_MESSAGE


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )


def hash_password(password: str) -> str:
    return bcrypt.hash(password)


def validate_token(token: str,
                   username: str,
                   user_id: int,) -> bool:
    payload = decode_token(token)
    token_username = payload['user']['username']
    token_user_id = payload['user']['id']
    if token_username != username or token_user_id != user_id:
        return False
    return True


async def add_users_to_database(users: Iterable[dict]) -> List[DBUser]:
    await database.connect()
    res = []
    for user in users:
        db_user = await DBUser.objects.create(
            username=user['username'],
            password_hash=hash_password(user['password'])
        )
        res.append(db_user)
    await database.disconnect()
    return res


def generate_user_login_data(user_data: dict) -> str:
    return f"username={user_data['username']}&password={user_data['password']}"


@pytest_asyncio.fixture
async def add_user_to_database() -> DBUser:
    await database.connect()

    user = await DBUser.objects.create(
        username='user',
        password_hash=hash_password('ag12')
    )

    return user


@pytest.fixture
def urlencoded_headers() -> dict:
    return {"Content-Type": "application/x-www-form-urlencoded"}


@pytest.fixture
def user_data() -> dict:
    return {'username': 'user', 'password': 'ag12'}


@pytest.mark.asyncio
async def test_route_sign_up_with_correct_data(user_data):
    with TestClient(app) as client:
        res = client.post('/auth/sign-up', json=user_data)

    assert res.json()['token_type'] == 'bearer'
    token = res.json()['access_token']

    await database.connect()
    users: List[DBUser] = await DBUser.objects.all()

    assert len(users) == 1
    user = users[0]
    assert user.username == user_data['username']
    assert validate_token(token, user.username, user.id)
    await database.disconnect()


@pytest.mark.asyncio
async def test_route_sign_up_with_duplicate_data(user_data):
    with TestClient(app) as client:
        client.post('/auth/sign-up', json=user_data)
        res = client.post('/auth/sign-up', json=user_data)

    await database.connect()
    users: List[DBUser] = await DBUser.objects.all()

    assert len(users) == 1
    assert res.json() == {"detail": INCORRECT_USERNAME_OR_PASS_MESSAGE}
    assert res.status_code == 422

    await database.disconnect()


@pytest.mark.asyncio
async def test_route_sign_in_with_correct_data(user_data: dict,
                                               urlencoded_headers: dict):
    users = await add_users_to_database((user_data,))
    user = users[0]
    login_data = generate_user_login_data(user_data)

    with TestClient(app) as client:
        res = client.post('/auth/sign-in',
                          data=login_data,
                          headers=urlencoded_headers)

    assert res.json()['token_type'] == 'bearer'
    token = res.json()['access_token']
    assert validate_token(token, user.username, user.id)


@pytest.mark.parametrize(
    ('delta_username', 'delta_password'),
    [('_name', ''),
     ('', '_pass'), ]
)
@pytest.mark.asyncio
async def test_route_sign_in_with_incorrect_data(user_data,
                                                 delta_username,
                                                 delta_password,
                                                 urlencoded_headers):
    await add_users_to_database((user_data,))

    user_data['username'] += delta_username
    user_data['password'] += delta_password

    login_data = generate_user_login_data(user_data)

    with TestClient(app) as client:
        res = client.post(url='/auth/sign-in',
                          data=login_data,
                          headers=urlencoded_headers)

    assert res.status_code == 401
    assert res.json() == {"detail": INCORRECT_USERNAME_OR_PASS_MESSAGE}


@pytest.mark.asyncio
async def test_auth_by_correct_token(user_data, urlencoded_headers):
    login_data = generate_user_login_data(user_data)
    users = await add_users_to_database((user_data,))
    user = users[0]

    with TestClient(app) as client:
        res = client.post(url='/auth/sign-in',
                          data=login_data,
                          headers=urlencoded_headers)

        token = res.json()['access_token']
        login_headers = {'Authorization': f'Bearer {token}'}
        res = client.get('/auth/user', headers=login_headers)
        res_data = res.json()

    assert res.status_code == 200
    assert res_data['id'] == user.id
    assert res_data['username'] == user_data['username']


@pytest.mark.asyncio
async def test_auth_by_incorrect_token(user_data):
    await add_users_to_database((user_data,))

    with TestClient(app) as client:
        token = 'fake_token'
        login_headers = {'Authorization': f'Bearer {token}'}
        res = client.get('/auth/user', headers=login_headers)

    assert res.status_code == 401
    assert res.json() == {'detail': INCORRECT_TOKEN_MESSAGE}
