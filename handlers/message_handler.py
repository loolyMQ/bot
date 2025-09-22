from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

from messages import BotMessages
from container import ContainerFactory
from interfaces import IUserService, ITarotService

router = Router()


def buy_messages_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=BotMessages.OPEN_APP,
            url="https://e696722740d6733ce8592753b9c29d4c.serveo.net"
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


@router.message(F.text)
async def handle_text_message(msg: Message):
    try:
        container = await ContainerFactory.create_container()
        user_service = container.get(IUserService)
        tarot_service = container.get(ITarotService)
        
        user = await user_service.get_or_create_user(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name
        )
        
        if not await user_service.can_send_message(user.user_id):
            await msg.answer(
                text=BotMessages.NO_MESSAGES_MESSAGE,
                reply_markup=buy_messages_keyboard()
            )
            return
        
        await msg.bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(2)
        
        partial_message = await msg.answer("✍️ пе")
        
        await asyncio.sleep(3)
        
        reading = await tarot_service.create_reading(
            user_id=user.user_id,
            question=msg.text,
            deck_type="rider_waite"
        )
        
        await user_service.consume_message(user.user_id)
        
        full_text = BotMessages.TAROT_READING_MESSAGE.format(
            question=msg.text,
            card=reading.card_name,
            interpretation=reading.interpretation,
            advice=reading.advice,
            remaining_messages=user.balance - 1
        )
        
        await partial_message.edit_text(full_text)
        
    except Exception as e:
        print(f"Error handling text message: {e}")
        await msg.answer(BotMessages.ERROR_OCCURRED)


@router.message(F.voice)
async def handle_voice_message(msg: Message):
    try:
        container = await ContainerFactory.create_container()
        user_service = container.get(IUserService)
        tarot_service = container.get(ITarotService)
        
        user = await user_service.get_or_create_user(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
            first_name=msg.from_user.first_name,
            last_name=msg.from_user.last_name
        )
        
        if not await user_service.can_send_message(user.user_id):
            await msg.answer(
                text=BotMessages.NO_MESSAGES_MESSAGE,
                reply_markup=buy_messages_keyboard()
            )
            return
        
        await msg.bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.RECORD_VOICE)
        await asyncio.sleep(2)
        
        partial_message = await msg.answer("✍️ пе")
        
        await asyncio.sleep(3)
        
        reading = await tarot_service.create_reading(
            user_id=user.user_id,
            question="Голосовое сообщение",
            deck_type="rider_waite"
        )
        
        await user_service.consume_message(user.user_id)
        
        full_text = BotMessages.VOICE_READING_MESSAGE.format(
            question="Голосовое сообщение",
            card=reading.card_name,
            remaining_messages=user.balance - 1
        )
        
        await partial_message.edit_text(full_text)
        
    except Exception as e:
        print(f"Error handling voice message: {e}")
        await msg.answer(BotMessages.ERROR_OCCURRED)


@router.callback_query(F.data == "buy_messages")
async def buy_messages_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        text=BotMessages.BUY_MESSAGES_CALLBACK,
        reply_markup=buy_messages_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "invite_friend")
async def invite_friend_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        text=BotMessages.INVITE_READY,
        reply_markup=buy_messages_keyboard()
    )
    await callback.answer()