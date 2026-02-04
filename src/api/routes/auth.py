from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependesies import get_uow_session
from api.schemas import TokenInfo, UserCreate, UserLogin, UserResponse
from services.auth_service import get_auth_service

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db_session: AsyncSession = Depends(get_uow_session),
):
    return await get_auth_service(db_session).register_user(user_data)


@router.post("/login", response_model=TokenInfo)
async def login_user(
    sign_in_data: UserLogin,
    db_session: AsyncSession = Depends(get_uow_session),
):
    return await get_auth_service(db_session).authenticate_user(sign_in_data)
