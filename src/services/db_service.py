from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories import Repository

REPOSITORY_TYPE = TypeVar("REPOSITORY_TYPE", bound=Repository)


class DbService(ABC, Generic[REPOSITORY_TYPE]):
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository: REPOSITORY_TYPE = self._create_repository()

    @abstractmethod
    def _create_repository(self) -> REPOSITORY_TYPE:
        raise NotImplementedError("The repository object must be defined in self.repository")
