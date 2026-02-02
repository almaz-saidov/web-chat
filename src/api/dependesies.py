from typing import AsyncIterator

from fastapi import Depends, WebSocket, WebSocketException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.unit_of_work import unit_of_work
from services.auth_service import get_auth_service

security = HTTPBearer()


async def get_uow_session() -> AsyncIterator[AsyncSession]:
    async with unit_of_work() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_session: AsyncSession = Depends(get_uow_session),
) -> User:
    auth_service = get_auth_service(db_session)
    return await auth_service.authorize_user(credentials.credentials)


async def get_current_user_from_ws(
    websocket: WebSocket,
    db_session: AsyncSession = Depends(get_uow_session),
) -> User:
    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Token is required",
        )

    try:
        auth_service = get_auth_service(db_session)
        return await auth_service.authorize_user(token)
    except ValueError as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        )
