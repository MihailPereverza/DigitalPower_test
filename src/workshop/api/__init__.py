from fastapi import APIRouter

from ..api.auth import router as auth_router
from ..api.emoticon import router as emoticon_router


router = APIRouter()
router.include_router(auth_router)
router.include_router(emoticon_router)
