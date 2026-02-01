from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependesies import get_uow_session
from api.schemas import TokenInfo, UserCreate, UserResponse, UserSignIn
from services.auth_service import get_auth_service

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db_session: AsyncSession = Depends(get_uow_session),
):
    auth_service = get_auth_service(db_session)
    return await auth_service.register_user(user_data)


@router.post("/sign_in", response_model=TokenInfo)
async def sign_in(
    sign_in_data: UserSignIn,
    db_session: AsyncSession = Depends(get_uow_session),
):
    auth_service = get_auth_service(db_session)
    return await auth_service.sign_in(sign_in_data)
