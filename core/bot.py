from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings

bot = Bot(
    token=settings.bot.TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)


def create_bot() -> Bot:
    return bot
