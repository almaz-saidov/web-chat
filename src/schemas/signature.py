import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.config import settings


class SignaturePointSchema(BaseModel):
    x: float
    y: float
    pressure: float = Field(..., ge=0, le=1)
    tilt_x: float = Field(..., ge=-90, le=90)
    tilt_y: float = Field(..., ge=-90, le=90)
    time_ms: float = Field(..., ge=0)


class SignatureSampleSchema(BaseModel):
    points: list[SignaturePointSchema] = Field(
        ..., min_length=settings.SIGNATURE_MIN_POINT_COUNT
    )
    duration_ms: float = Field(..., gt=0)
    break_count: int = Field(..., ge=0)


class SignatureTemplateDataSchema(BaseModel):
    points: list[SignaturePointSchema] = Field(
        ..., min_length=settings.SIGNATURE_MIN_POINT_COUNT
    )
    duration_ms: float = Field(..., gt=0)
    break_count: float = Field(..., ge=0)


class SignatureTemplateCreateSchema(BaseModel):
    user_id: uuid.UUID
    template_data: SignatureTemplateDataSchema


class SignatureTemplateSchema(SignatureTemplateCreateSchema):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
