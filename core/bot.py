import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from core.handlers import register_handlers
from core.admin import AdminPanel
from utils.regex import SpamFilter

class SpamBot:
    def __init__(self, bot_token, spam_filter, ban_duration_days, mute_duration_days, dp):
        """
        Initialize the bot
        :param bot_token: Telegram bot token
        :param spam_filter: SpamFilter object
        :param ban_duration_days: Duration of ban in days
        :param mute_duration_days: Duration of mute in days
        :param dp: Dispatcher object
        """
        self.ban_duration_days = ban_duration_days
        self.mute_duration_days = mute_duration_days
        self.bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode="HTML"))
        self.dp = dp
        self.spam_filter = spam_filter
        self.ban_duration_days = ban_duration_days
        self.mute_duration_days = mute_duration_days
        self.admin_panel = AdminPanel(self.bot, self.dp, self.spam_filter, self.ban_duration_days,
                                      self.mute_duration_days)
    async def start_polling(self):
        """Starts the bot polling."""
        # Спочатку реєструємо обробники команд (більш специфічні)
        self.admin_panel.register_admin_handlers()
        
        # Потім реєструємо загальний обробник для спаму (менш специфічний)
        register_handlers(self.dp, self.bot, self.spam_filter, self.ban_duration_days, self.mute_duration_days, self.admin_panel)
        
        print("Starting polling...")
        await self.dp.start_polling(self.bot)
        print("Bot stopped")

    async def stop(self):
        """Stops the bot."""
        await self.bot.close()