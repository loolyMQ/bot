from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from messages import BotMessages
from container import ContainerFactory
from interfaces import IUserService

router = Router()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=BotMessages.OPEN_APP,
            url="https://e696722740d6733ce8592753b9c29d4c.serveo.net"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=BotMessages.BUY_MESSAGES,
            callback_data="buy_messages"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=BotMessages.INVITE_FRIEND,
            callback_data="invite_friend"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=BotMessages.BACK,
            callback_data="back_to_menu"
        )
    )
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_callback(callback: CallbackQuery):
    try:
        container = await ContainerFactory.create_container()
        user_service = container.get(IUserService)
        
        user = await user_service.get_or_create_user(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name
        )
        
        await callback.message.edit_text(
            text=f"🏠 Главное меню:\n\nВаш баланс: {user.balance} сообщений",
            reply_markup=main_menu_keyboard()
        )
        await callback.answer()
    except Exception as e:
        print(f"Error in back_to_menu_callback: {e}")
        await callback.answer("Произошла ошибка")