from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import UserCreate, UserResponse
from database.unit_of_work import get_uow_session
from services.auth_service import get_auth_service

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db_session: AsyncSession = Depends(get_uow_session),
):
    auth_service = get_auth_service(db_session)
    return await auth_service.register_user(user_data)
