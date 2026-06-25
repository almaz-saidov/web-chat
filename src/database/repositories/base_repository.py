from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db_session


class BaseDatabaseRepository:
    _session: AsyncSession

    def __init__(self, session: AsyncSession = Depends(get_db_session)) -> None:
        self._session = session
