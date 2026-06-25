from typing import Generic, TypeVar

from database.repositories.base_repository import BaseDatabaseRepository

REPOSITORY_TYPE = TypeVar("REPOSITORY_TYPE", bound=BaseDatabaseRepository)


class DatabaseService(Generic[REPOSITORY_TYPE]):
    def __init__(self, repository: REPOSITORY_TYPE) -> None:
        self._repository = repository
