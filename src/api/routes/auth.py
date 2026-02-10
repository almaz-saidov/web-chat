from fastapi import APIRouter, Depends, Request, Response

from api.schemas import (LocalStorageUserData, TokenInfo, UserCreate,
                         UserLogin, UserResponse)
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
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.authenticate_user(login_data, response)


@router.post("/refresh", response_model=TokenInfo)
async def refresh_tokens(
    user_data: LocalStorageUserData,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.refresh_tokens(user_data, request, response)
