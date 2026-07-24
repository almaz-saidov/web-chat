from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from schemas.message import MessageCreateSchema, MessageSchema
from schemas.user import UserSchema
from services.message_service import MessageService

router = APIRouter(prefix="/message", tags=["Messages"])


@router.get("/all", response_model=list[MessageSchema])
async def get_messages(
    user: UserSchema = Depends(get_current_user),
    message_service: MessageService = Depends(),
) -> list[MessageSchema]:
    return await message_service.get_all()


@router.post("/create", response_model=MessageSchema)
async def create_message(
    message_create_data: MessageCreateSchema,
    user: UserSchema = Depends(get_current_user),
    message_service: MessageService = Depends(),
) -> MessageSchema:
    return await message_service.create(
        message_create_data=message_create_data, user=user
    )
