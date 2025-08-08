import asyncio
import os
from dotenv import load_dotenv
from aiogram import Dispatcher

from core import SpamBot
from models import BAN_DURATION_DAYS, ADMIN_IDS, MUTE_DURATION_DAYS
from utils import SpamFilter

async def main():
    """main function to start bot"""
    print("Bot is starting...")

    # Load environment variables
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set in .env file")

    # Check if admin IDs are configured
    if not ADMIN_IDS:
        print("⚠️  Warning: No admin IDs configured. Add ADMIN_IDS to your .env file")
        print("   Example: ADMIN_IDS=123456789,987654321")
        print("   Use /my_id command to get your Telegram ID")

    # Initialize SpamFilter (фільтри завантажуються з filters.json)
    spam_filter = SpamFilter()

    # Initialize Dispatcher
    dp = Dispatcher()

    # Initialize and run the bot
    spam_bot = SpamBot(bot_token, spam_filter, BAN_DURATION_DAYS, MUTE_DURATION_DAYS, dp)
    await spam_bot.start_polling()
    
if __name__ == "__main__":
    asyncio.run(main())