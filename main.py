from datetime import datetime, timedelta
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums.chat_member_status import ChatMemberStatus
from dotenv import load_dotenv

# Dovnolad enviroment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# regular expression for spam message
# Find words "рубль", "рубли", "рублей" in message with latin and cyrillic letters
SPAM_PATTERN = re.compile(r'([рp][уy]бл[еe][йия]?)|([уy]д[аa]л[еe]нн[оo])|(₽)|(\$)', re.IGNORECASE)

@dp.message()
async def handle_all_messages(message: types.Message):
    """
    Habdler for all messages in all chats.
    If message contains spam, it will be deleted and user will be banned for 30 days.
    If user is admin or owner message will be deleted only (without banning)
    """
    if message.text:
        if SPAM_PATTERN.search(message.text):
            try:
                # First delete message, then get chat member status
                await message.delete()
                print(f"Deleted message from {message.from_user.username}: {message.text}")
                
                # Get chat member status
                chat_member = await bot.get_chat_member(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id
                )
                
                # Check if user is admin or owner
                if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                    await bot.ban_chat_member(
                        chat_id=message.chat.id,
                        user_id=message.from_user.id,
                        until_date=datetime.now() + timedelta(days=30)
                    )
                    print(f"Banned user {message.from_user.username}")
                else:
                    print(f"User {message.from_user.username} is {chat_member.status.value}")
            except Exception as e:
                print(f"Error deleting message or banning user: {e}")
                
async def main():
    """main function to start bot"""
    print("Bot is starting...")
    await dp.start_polling(bot)
    print("Bot is stopped")


if __name__ == "__main__":
    asyncio.run(main())
