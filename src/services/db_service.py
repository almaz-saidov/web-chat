from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.base_repository import BaseRepository

REPOSITORY_TYPE = TypeVar("REPOSITORY_TYPE", bound=BaseRepository)


class DatabaseService(ABC, Generic[REPOSITORY_TYPE]):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repository: REPOSITORY_TYPE = self._create_repository()

    @abstractmethod
    def _create_repository(self) -> REPOSITORY_TYPE:
        raise NotImplementedError("The repository object must be defined in self.repository")
