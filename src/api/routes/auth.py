from fastapi import APIRouter, Depends, Request, Response, status

from api.schemas import (AccessTokenSchema, LocalStorageUserSchema,
                         UserCreateSchema, UserLoginSchema, UserResponseSchema)
from services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["Authorization"])


@router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreateSchema,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.register_user(user_data=user_data)


@router.post("/login", response_model=AccessTokenSchema, status_code=status.HTTP_200_OK)
async def login_user(
    login_data: UserLoginSchema,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.authenticate_user(login_data=login_data, response=response)


@router.post("/refresh", response_model=AccessTokenSchema, status_code=status.HTTP_200_OK)
async def refresh_tokens(
    user_data: LocalStorageUserSchema,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    return await auth_service.refresh_tokens(user_data=user_data, request=request, response=response)
