from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from messages import BotMessages
from container import ContainerFactory
from interfaces import IUserService

router = Router()


def welcome_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=BotMessages.START_BUTTON,
            callback_data="start"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


@router.message(CommandStart)
async def start_command(msg: Message):
    try:
        container = await ContainerFactory.create_container()
        user_service = container.get(IUserService)
        
        user = await user_service.get_or_create_user(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name
        )
        
        await msg.answer(
            text=BotMessages.WELCOME_MESSAGE,
            reply_markup=welcome_keyboard()
        )
    except Exception as e:
        print(f"Error sending start message: {e}")
        await msg.answer(BotMessages.ERROR_OCCURRED)

