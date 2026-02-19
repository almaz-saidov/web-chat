from fastapi import APIRouter, Depends, Request, Response, status

from api.schemas import (AccessTokenSchema, UserCreateSchema, UserLoginSchema,
                         UserResponseSchema)
from services.auth_service import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["Authorization"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchema)
async def register_user(
    user_create_data: UserCreateSchema,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponseSchema:
    return await auth_service.register_user(user_create_data=user_create_data)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=AccessTokenSchema)
async def login_user(
    login_data: UserLoginSchema,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> AccessTokenSchema:
    return await auth_service.authenticate_user(login_data=login_data, response=response)


@router.post("/refresh", status_code=status.HTTP_200_OK, response_model=AccessTokenSchema)
async def refresh_tokens(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> AccessTokenSchema:
    return await auth_service.refresh_tokens(request=request, response=response)
