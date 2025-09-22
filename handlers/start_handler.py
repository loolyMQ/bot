from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from container import ContainerFactory
from messages import BotMessages
from interfaces import IUserService


router = Router()


class StartStates(StatesGroup):
    waiting_for_name = State()


@router.message(CommandStart())
async def handle_start_command(message: Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        
        container = await ContainerFactory.create_container()
        user_service = container.get(IUserService)
        
        user = await user_service.get_or_create_user(user_id=user_id)
        
        if user:
            welcome_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=BotMessages.BUY_MESSAGES, callback_data="buy_messages")],
                    [InlineKeyboardButton(text=BotMessages.INVITE_FRIEND, callback_data="invite_friend")],
                    [InlineKeyboardButton(text=BotMessages.OPEN_APP, callback_data="open_app")]
                ]
            )
            
            await message.answer(
                BotMessages.WELCOME_MESSAGE.format(balance=user.balance),
                reply_markup=welcome_keyboard
            )
        else:
            await message.answer(BotMessages.ERROR_OCCURRED)
            
    except Exception as e:
        print(f"Error in start handler: {e}")
        await message.answer(BotMessages.ERROR_OCCURRED)


