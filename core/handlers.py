import asyncio
from datetime import datetime, timedelta
from functools import partial
from aiogram import Bot, Dispatcher, types
from aiogram.enums.chat_member_status import ChatMemberStatus
from utils.regex import SpamFilter

async def handle_all_messages(
    message: types.Message, 
    bot: Bot, 
    spam_filter: SpamFilter,
    ban_duration_days: int,
    mute_duration_days: int,
    admin_panel=None
):
    """
    Handler for all messages in all chats.
    If message contains spam, it will be deleted and the user will be banned for 30 days.
    If the user is an admin or owner, the message will be deleted only (without banning).
    """
    # Логуємо всі повідомлення для діагностики
    print(f"Handling message: {message.text} from {message.from_user.username} in {message.chat.title}")
    
    # Skip messages related to FSM states
    if admin_panel and message.from_user.id in admin_panel.pending_actions:
        return

    if message.text and spam_filter.is_spam(message.text):
        print(f"SPAM DETECTED: {message.text}")
        try:
            # Пересилаємо повідомлення адміну ПЕРЕД видаленням
            if admin_panel:
                await admin_panel.forward_deleted_message(
                    message, 
                    message.chat.id, 
                    message.from_user.id
                )

            # Тепер видаляємо повідомлення
            await message.delete()
            print(f"Deleted message from {message.from_user.username}: {message.text}")

            chat_member = await bot.get_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id
            )

            if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                await bot.restrict_chat_member(
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    permissions=types.ChatPermissions(
                        can_send_messages=False,
                        can_send_media_messages=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                    ),
                    until_date=datetime.now() + timedelta(days=mute_duration_days)
                )
                print(f"Banned user {message.from_user.username}")
            else:
                print(f"User {message.from_user.username} is {chat_member.status.value}. Message deleted, but not banned.")

        except Exception as e:
            print(f"Error deleting message or banning user: {e}")
    else:
        print(f"Message is not spam: {message.text}")

def register_handlers(dp: Dispatcher, bot: Bot, spam_filter: SpamFilter, ban_duration_days: int, mute_duration_days: int, admin_panel=None):
    """Register all handlers for the bot."""
    dp.message.register(
        partial(
            handle_all_messages,
            bot=bot,
            spam_filter=spam_filter,
            ban_duration_days=ban_duration_days,
            mute_duration_days=mute_duration_days,
            admin_panel=admin_panel
        )
    )
