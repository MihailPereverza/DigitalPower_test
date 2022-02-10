from fastapi import APIRouter
from fastapi import Depends
from fastapi import Body
from fastapi.security import OAuth2PasswordRequestForm

from ..models.auth import UserCreate, User
from ..models.auth import Token
from ..services.auth import AuthService, get_current_user


router = APIRouter(
    prefix='/auth'
)


@router.post('/sign-up', response_model=Token)
async def sign_up(
        user_data: UserCreate = Body(None),
        service: AuthService = Depends(), # noqa
) -> Token:
    return await service.register_new_user(user_data)


@router.post('/sign-in', response_model=Token)
async def sign_in(
        form_data: OAuth2PasswordRequestForm = Depends(),
        service: AuthService = Depends(),
):
    return await service.authenticate_user(
        form_data.username,
        form_data.password,
    )


@router.get('/user', response_model=User)
def get_user(user: User = Depends(get_current_user)):
    return user
