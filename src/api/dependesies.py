from fastapi import Depends, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.exceptions import TokenIsRequiredWebSocketException
from schemas.user import UserSchema
from services.auth_service import AuthService, get_auth_service

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        auth_service: AuthService = Depends(get_auth_service),
) -> UserSchema:
    return await auth_service.authorize_user(credentials.credentials)


async def get_current_user_from_ws(
        websocket: WebSocket,
        auth_service: AuthService = Depends(get_auth_service),
) -> UserSchema:
    token = websocket.query_params.get("token")

    if not token:
        raise TokenIsRequiredWebSocketException()

    user = await auth_service.authorize_websocket_user(token)
    return user
