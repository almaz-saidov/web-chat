from fastapi import Depends, WebSocket, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.models import User
from services.auth_service import AuthService, get_auth_service

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    return await auth_service.authorize_user(credentials.credentials)


async def get_current_user_from_ws(
    websocket: WebSocket,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Token is required",
        )

    return await auth_service.authorize_user(token)
