from typing import Generic, Type, TypeVar, cast

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import Base

MODEL_TYPE = TypeVar("MODEL_TYPE", bound=Base)


class Repository(Generic[MODEL_TYPE]):
    _cls_model: Type[MODEL_TYPE] | None = None

    def __init__(self, session: AsyncSession, model: Type[MODEL_TYPE] | None = None) -> None:
        self._session = session
        self._model: Type[MODEL_TYPE]

        if model:
            self._model = model
        elif self._cls_model:
            self._model = self._cls_model
        else:
            raise ValueError("Необходимо передать модель в __init__ или определить _cls_model в классе")


class InsertOneRepository(Repository[MODEL_TYPE]):
    async def insert_one(self, data: dict) -> MODEL_TYPE:
        stmt = insert(self._model).values(**data).returning(self._model)
        result = await self._session.execute(stmt)

        return result.scalar_one()


class SelectOneRepository(Repository[MODEL_TYPE]):
    async def select_one(self, **filter_by) -> MODEL_TYPE | None:
        stmt = select(self._model).filter_by(**filter_by).limit(1)
        result = await self._session.execute(stmt)

        return result.scalar_one_or_none()


class SelectAllRepository(Repository[MODEL_TYPE]):
    async def select_all(self, **filter_by) -> list[MODEL_TYPE]:
        stmt = select(self._model).filter_by(**filter_by)
        result = await self._session.execute(stmt)

        return cast(list[MODEL_TYPE], result.scalars().all())


class ForceDeleteRepository(Repository[MODEL_TYPE]):
    async def force_delete(self, **filter_by) -> None:
        stmt = delete(self._model).filter_by(**filter_by)

        await self._session.execute(stmt)
