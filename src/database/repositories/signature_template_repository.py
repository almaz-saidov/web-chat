import uuid

from sqlalchemy import insert, select

from database.models import SignatureTemplate
from database.repositories.base_repository import BaseDatabaseRepository
from schemas.signature import SignatureTemplateCreateSchema, SignatureTemplateSchema


class SignatureTemplateRepository(BaseDatabaseRepository):
    async def create(self, signature_template_create_data: SignatureTemplateCreateSchema) -> SignatureTemplateSchema:
        query = (
            insert(SignatureTemplate).values(**signature_template_create_data.model_dump()).returning(SignatureTemplate)
        )

        result = await self._session.execute(query)
        signature_template = result.scalar_one()

        return SignatureTemplateSchema.model_validate(signature_template)

    async def get_by_user_id(self, user_id: uuid.UUID) -> SignatureTemplateSchema | None:
        query = select(SignatureTemplate).where(SignatureTemplate.user_id == user_id)

        result = await self._session.execute(query)
        signature_template = result.scalar_one_or_none()

        return SignatureTemplateSchema.model_validate(signature_template) if signature_template else None
