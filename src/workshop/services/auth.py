import logging
from datetime import datetime, timedelta

from asyncpg import UniqueViolationError
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ormar import NoMatch
from passlib.hash import bcrypt
from fastapi import HTTPException
from fastapi import Depends
from fastapi import status
from pydantic import ValidationError

from ..models.auth import User
from ..models.auth import UserCreate
from ..models.auth import Token
from ..settings import settings
from ..db.User import User as DBUser
from ..constants import INCORRECT_USERNAME_OR_PASS_MESSAGE
from ..constants import INCORRECT_TOKEN_MESSAGE


class AuthService:
    @classmethod
    def validate_password(cls, password: str) -> bool:
        return len(password) >= 4

    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return bcrypt.verify(password, hashed_password)

    @classmethod
    def hash_password(cls, password: str) -> str:
        return bcrypt.hash(password)

    @classmethod
    def validate_token(cls, token: str) -> User:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_TOKEN_MESSAGE,
            headers={
                'WWW-Authenticate': 'Bearer',
            },
        )

        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError:
            raise exception from None

        user_data = payload.get('user')

        try:
            user = User.parse_obj(user_data)
        except ValidationError:
            raise exception from None

        return user

    @classmethod
    def create_token(cls, user: DBUser) -> Token:
        user_data = User.from_orm(user)

        now = datetime.utcnow()
        payload = {
            'iat': now,
            'nbf': now,
            'exp': now + timedelta(seconds=settings.jwt_expiration),
            'sub': str(user_data.id),
            'user': user_data.dict(),
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        return Token(access_token=token)

    def __init__(self):
        self.logger = logging.getLogger('main.auth_service')

    async def register_new_user(self, user_data: UserCreate) -> Token:
        exception = HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=INCORRECT_USERNAME_OR_PASS_MESSAGE,
        )

        if not self.validate_password(user_data.password):
            raise exception from None

        try:
            user = await DBUser.objects.create(
                username=user_data.username,
                password_hash=self.hash_password(user_data.password)
            )
        except UniqueViolationError:
            self.logger.info('Failed to save new user to database')
            raise exception from None

        return self.create_token(user)

    async def authenticate_user(self, username: str, password: str) -> Token:
        exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INCORRECT_USERNAME_OR_PASS_MESSAGE,
            headers={
                'WWW-Authenticate': 'Bearer',
            },
        )

        try:
            user = await DBUser.objects.get(username=username)
        except NoMatch:
            self.logger.info('Not found user by login-password')
            raise exception from None

        if not self.verify_password(password, user.password_hash):
            self.logger.info(f"Didn't verify the pass of the user {username}")
            raise exception from None

        print(username)
        self.logger.info(f'User {username} is logged in')
        return self.create_token(user)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/sign-in/')


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    return AuthService.validate_token(token)
