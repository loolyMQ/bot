import asyncio

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommandScopeDefault

from handlers.start_handler import router as start_router
from handlers.message_handler import router as message_router
from handlers.callback_handler import router as callback_router
from config import settings
from core.bot import bot
from core.logger import setup_logging

dp = Dispatcher(
    bot=bot,
    storage=MemoryStorage()
)

dp.include_router(start_router)
dp.include_router(message_router)
dp.include_router(callback_router)


async def startup(bot: Bot) -> None:
    await bot.delete_webhook()
    await bot.set_my_commands(
        commands=[
            {"command": "start", "description": "Начать работу с ботом"}
        ],
        scope=BotCommandScopeDefault()
    )
    print('=== Arcana Bot started ===')


async def shutdown(bot: Bot) -> None:
    await bot.close()
    await dp.stop_polling()
    print('=== Arcana Bot stopped ===')


async def main() -> None:
    setup_logging()
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
