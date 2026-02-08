from fastapi import APIRouter, Depends

from api.schemas import TokenInfo, UserCreate, UserLogin, UserResponse
from services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=TokenInfo)
async def login_user(
    login_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.authenticate_user(login_data)
