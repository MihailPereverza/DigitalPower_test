from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from ..models.auth import User
from ..services.auth import get_current_user
from ..services.emoticon import EmoticonService

router = APIRouter(
    prefix='/emoticon'
)


@router.get('/')
async def emoticon(
        username: str = Query(None, description='Логин пользователя'),
        user: User = Depends(get_current_user),
        service: EmoticonService = Depends(),
):
    await service.validate_data(user.username, username)
    return await service.get_user_emoticon(user.username)
