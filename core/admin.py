import asyncio
import json
from datetime import datetime, timedelta
from typing import Any
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums.chat_member_status import ChatMemberStatus
from models.settings import ADMIN_IDS, add_dynamic_admin, remove_dynamic_admin, is_env_admin, get_dynamic_admin_ids, \
    get_admin_ids, get_all_admin_ids

class AdminStates(StatesGroup):
    waiting_for_word_to_add = State()
    waiting_for_word_to_remove = State()
    waiting_for_admin_id_to_add = State()
    waiting_for_admin_id_to_remove = State()
    waiting_for_char_to_add = State()
    waiting_for_mapping_to_add = State()
    waiting_for_char_to_remove = State()
    waiting_for_mapping_to_remove = State()

def make_user_tag(user: types.User) -> str:
    """Повертає тегований username або лінк на користувача для Markdown."""
    if user.username:
        # Без @ якщо username починається з @, інакше додаємо @
        safe_username = user.username.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
        return f"@{safe_username}"
    name = user.first_name or "User"
    # Екрануємо спецсимволи для Markdown
    safe_name = name.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
    return f"[{safe_name}](tg://user?id={user.id})"

class AdminPanel:
    def __init__(self, bot: Bot, dp: Dispatcher, spam_filter, ban_duration_days: int, mute_duration_days: int):
        self.ban_duration_days = ban_duration_days
        self.mute_duration_days = mute_duration_days
        self.bot = bot
        self.dp = dp
        self.admin_ids = ADMIN_IDS
        self.spam_filter = spam_filter
        self.deleted_messages: dict[int, dict[str, Any]] = {}  # Зберігаємо інформацію про видалені повідомлення
        self.pending_actions: dict[str, dict[str, Any]] = {}   # Для сумісності з handler
        self.cleanup_old_messages()

    def cleanup_old_messages(self):
        current_time = datetime.now()
        old_messages = []
        for msg_id, msg_info in self.deleted_messages.items():
            if (current_time - msg_info['timestamp']).total_seconds() > 86400:
                old_messages.append(msg_id)
        for msg_id in old_messages:
            del self.deleted_messages[msg_id]
        if old_messages:
            print(f"Cleaned up {len(old_messages)} old messages")

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    async def admin_menu(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Управління словами", callback_data="admin_words")],
            [InlineKeyboardButton(text="👑 Управління адміністраторами", callback_data="admin_management")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🆔 Мій ID", callback_data="admin_my_id")]
        ])
        await message.answer(
            "🔧 **Адмін-панель**\n\nОберіть розділ для управління:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    def register_admin_handlers(self):
        self.dp.message.register(self.admin_menu, Command("admin"))
        self.dp.message.register(self.admin_add_word, Command("add_word"))
        self.dp.message.register(self.admin_remove_word, Command("remove_word"))
        self.dp.message.register(self.admin_list_words, Command("list_words"))
        self.dp.message.register(self.admin_management, Command("admins"))
        self.dp.message.register(self.admin_add_admin, Command("add_admin"))
        self.dp.message.register(self.admin_remove_admin, Command("remove_admin"))
        self.dp.message.register(self.admin_add_chat_admins, Command("add_chat_admins"))
        self.dp.message.register(self.get_my_id, Command("my_id"))
        self.dp.callback_query.register(self.handle_admin_callback)
        # FSM
        self.dp.message.register(self.process_add_word, AdminStates.waiting_for_word_to_add)
        self.dp.message.register(self.process_remove_word, AdminStates.waiting_for_word_to_remove)
        self.dp.message.register(self.process_add_admin, AdminStates.waiting_for_admin_id_to_add)
        self.dp.message.register(self.process_remove_admin, AdminStates.waiting_for_admin_id_to_remove)
        # FSM для карти символів
        self.dp.message.register(self.process_add_char, AdminStates.waiting_for_char_to_add)
        self.dp.message.register(self.process_add_mapping, AdminStates.waiting_for_mapping_to_add)
        self.dp.message.register(self.process_remove_char, AdminStates.waiting_for_char_to_remove)
        self.dp.message.register(self.process_remove_mapping, AdminStates.waiting_for_mapping_to_remove)

    async def forward_reported_message(self, message: types.Message, chat_id: int, user_id: int, reporter_id: int):
        """
        Пересилає повідомлення, на яке поскаржився користувач, всім адміністраторам
        """
        try:
            message_info = {
                'user_id': user_id,
                'chat_id': chat_id,
                'text': message.text,
                'timestamp': datetime.now(),
                'user_username': message.from_user.username,
                'user_first_name': message.from_user.first_name,
                'user_last_name': message.from_user.last_name,
                'chat_title': message.chat.title,
                'chat_username': message.chat.username,
                'message_id': message.message_id,
                'reporter_id': reporter_id
            }
            self.deleted_messages[message.message_id] = message_info
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚫 Забанити", callback_data=f"ban_user:{user_id}:{chat_id}"),
                    InlineKeyboardButton(text="🔇 Заглушити", callback_data=f"mute_user:{user_id}:{chat_id}")
                ],
                [
                    InlineKeyboardButton(text="❌ Видалити", callback_data=f"delete_msg:{message.message_id}:{chat_id}"),
                    InlineKeyboardButton(text="✅ Ігнорувати", callback_data=f"ignore_report:{message.message_id}:{chat_id}")
                ]
            ])
            
            # Отримуємо інформацію про користувача, який поскаржився
            try:
                reporter = await self.bot.get_chat_member(chat_id, reporter_id)
                reporter_display = make_user_tag(reporter.user)
            except:
                reporter_display = f"ID: {reporter_id}"
            
            user_display = make_user_tag(message.from_user)
            chat_display = message_info['chat_title'] or message_info['chat_username'] or f"Chat{chat_id}"
            # Важливо: екранувати текст повідомлення для Markdown!
            safe_text = (message.text or "").replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
            
            admin_message_text = (
                f"⚠️ **СКАРГА НА ПОВІДОМЛЕННЯ**\n\n"
                f"👤 **Користувач:** {user_display}\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"🕵️ **Скаржник:** {reporter_display}\n"
                f"💬 **Чат:** {chat_display}\n"
                f"📅 **Час:** {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"📝 **Текст повідомлення:**\n`{safe_text}`"
            )
            
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Error sending report to admin {admin_id}: {e}")
        except Exception as e:
            print(f"Error processing reported message: {e}")
            
    async def forward_deleted_message(self, message: types.Message, chat_id: int, user_id: int):
        try:
            message_info = {
                'user_id': user_id,
                'chat_id': chat_id,
                'text': message.text,
                'timestamp': datetime.now(),
                'user_username': message.from_user.username,
                'user_first_name': message.from_user.first_name,
                'user_last_name': message.from_user.last_name,
                'chat_title': message.chat.title,
                'chat_username': message.chat.username,
                'message_id': message.message_id
            }
            self.deleted_messages[message.message_id] = message_info
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🚫 Забанити", callback_data=f"ban_user:{user_id}:{chat_id}"),
                    InlineKeyboardButton(text="✅ Повернути",
                                         callback_data=f"restore_msg:{message.message_id}:{chat_id}")
                ]
            ])
            user_display = make_user_tag(message.from_user)
            chat_display = message_info['chat_title'] or message_info['chat_username'] or f"Chat{chat_id}"
            # Важливо: екранувати текст повідомлення для Markdown!
            safe_text = (message.text or "").replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
            admin_message_text = (
                f"🔍 **Видалене повідомлення**\n\n"
                f"👤 **Користувач:** {user_display}\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"💬 **Чат:** {chat_display}\n"
                f"📅 **Час:** {datetime.now().strftime('%H:%M:%S')}\n\n"
                f"📝 **Текст:**\n`{safe_text}`"
            )
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message_text,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Error sending message to admin {admin_id}: {e}")
        except Exception as e:
            print(f"Error processing deleted message: {e}")

    async def handle_admin_callback(self, callback: types.CallbackQuery, state: FSMContext):
        if not self.is_admin(callback.from_user.id):
            await callback.answer("❌ Доступ заборонено")
            return
        data = callback.data
        if data == "admin_words":
            await self.show_words_menu(callback)
        elif data == "admin_management":
            await self.show_admin_management(callback)
        elif data == "admin_stats":
            await self.show_stats(callback)
        elif data == "admin_my_id":
            await self.show_my_id(callback)
        elif data == "admin_main":
            await self.admin_main_callback(callback)
        elif data == "add_word_btn":
            await self.start_add_word(callback, state)
        elif data == "remove_word_btn":
            await self.start_remove_word(callback, state)
        elif data == "list_words_btn":
            await self.show_words_list(callback)
        elif data == "add_admin_btn":
            await self.start_add_admin(callback, state)
        elif data == "remove_admin_btn":
            await self.start_remove_admin(callback, state)
        elif data == "add_chat_admins":
            await self.add_chat_admins_callback(callback)
        elif data.startswith("ban_user:"):
            await self.ban_user_from_callback(callback, data)
        elif data.startswith("restore_msg:"):
            await self.restore_message_from_callback(callback, data)
        elif data.startswith("delete_msg:"):
            await self.delete_reported_message(callback, data)
        elif data.startswith("ignore_report:"):
            await self.ignore_report(callback, data)
        elif data.startswith("mute_user:"):
            await self.mute_user_from_callback(callback, data)
        elif data == "char_map_btn":
            await self.show_char_map_menu(callback)
        elif data == "add_char_btn":
            await self.start_add_char(callback, state)
        elif data == "remove_char_btn":
            await self.start_remove_char(callback, state)
        elif data == "list_chars_btn":
            await self.show_char_list(callback)
        else:
            await callback.answer("❌ Невідома дія")

    async def admin_main_callback(self, callback: types.CallbackQuery):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Управління словами", callback_data="admin_words")],
            [InlineKeyboardButton(text="👑 Управління адміністраторами", callback_data="admin_management")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🆔 Мій ID", callback_data="admin_my_id")]
        ])
        await callback.message.edit_text(
            "🔧 **Адмін-панель**\n\nОберіть розділ для управління:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def show_words_menu(self, callback: types.CallbackQuery):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати слово", callback_data="add_word_btn")],
            [InlineKeyboardButton(text="➖ Видалити слово", callback_data="remove_word_btn")],
            [InlineKeyboardButton(text="📋 Список слів", callback_data="list_words_btn")],
            [InlineKeyboardButton(text="🔡 Управління символами", callback_data="char_map_btn")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
        ])
        await callback.message.edit_text(
            "📋 **Управління словами фільтрації**\n\nОберіть дію:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def show_admin_management(self, callback: types.CallbackQuery):
        env_admins = get_admin_ids()
        dynamic_admins = get_dynamic_admin_ids()
        env_text = "\n".join([f"• {admin_id} (з .env)" for admin_id in env_admins]) if env_admins else "Немає"
        dynamic_text = "\n".join(
            [f"• {admin_id} (динамічний)" for admin_id in dynamic_admins]) if dynamic_admins else "Немає"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати адміністратора", callback_data="add_admin_btn")],
            [InlineKeyboardButton(text="➖ Видалити адміністратора", callback_data="remove_admin_btn")],
            [InlineKeyboardButton(text="👥 Додати адміністраторів чату", callback_data="add_chat_admins")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
        ])
        await callback.message.edit_text(
            f"👑 **Управління адміністраторами**\n\n"
            f"📋 **Адміністратори з .env:**\n{env_text}\n\n"
            f"📋 **Динамічні адміністратори:**\n{dynamic_text}\n\n"
            f"💡 *Адміністратори з .env не можна видаляти*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def show_stats(self, callback: types.CallbackQuery):
        patterns = self.spam_filter.get_patterns()
        env_admins = get_admin_ids()
        dynamic_admins = get_dynamic_admin_ids()
        stats_text = f"""
📊 **Статистика бота**

🔍 **Фільтри:**
• Слів фільтрації: {len(patterns)}
• Базових фільтрів: 4 (з filters.json)

👑 **Адміністратори:**
• З .env: {len(env_admins)}
• Динамічних: {len(dynamic_admins)}
• Всього: {len(env_admins) + len(dynamic_admins)}

🤖 **Статус:** Активний
📅 **Дата:** {datetime.now().strftime('%d.%m.%Y')}
⏰ **Час:** {datetime.now().strftime('%H:%M:%S')}
        """
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
        ])
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def show_my_id(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        username = callback.from_user.username or callback.from_user.first_name
        is_admin = self.is_admin(user_id)
        admin_status = "👑 **Адміністратор**" if is_admin else "👤 **Користувач**"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")]
        ])
        await callback.message.edit_text(
            f"🆔 **Ваш ID:** `{user_id}`\n"
            f"👤 **Ім'я:** {username}\n"
            f"📊 **Статус:** {admin_status}\n\n"
            f"💡 *Щоб додати себе як адміністратора, додайте ваш ID до ADMIN_IDS в .env файлі:*\n"
            f"`ADMIN_IDS={user_id}` або `ADMIN_IDS=123456789,{user_id}`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def start_add_word(self, callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "📝 Введіть слово або регулярний вираз для додавання до списку фільтрації:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_words")]
            ])
        )
        await state.set_state(AdminStates.waiting_for_word_to_add)

    async def start_remove_word(self, callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "🗑 Введіть слово для видалення зі списку фільтрації:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_words")]
            ])
        )
        await state.set_state(AdminStates.waiting_for_word_to_remove)

    async def show_words_list(self, callback: types.CallbackQuery):
        patterns = self.spam_filter.get_patterns()
        if patterns:
            patterns_text = "\n".join([f"• {pattern}" for pattern in patterns])
            text = f"📋 **Список слів фільтрації:**\n\n{patterns_text}"
        else:
            text = "📋 Список слів фільтрації порожній"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_words")]
        ])
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def start_add_admin(self, callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "🆔 Введіть ID користувача для додавання як адміністратора:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_management")]
            ])
        )
        await state.set_state(AdminStates.waiting_for_admin_id_to_add)

    async def start_remove_admin(self, callback: types.CallbackQuery, state: FSMContext):
        await callback.message.edit_text(
            "🆔 Введіть ID користувача для видалення з адміністраторів:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_management")]
            ])
        )
        await state.set_state(AdminStates.waiting_for_admin_id_to_remove)

    async def mute_user_from_callback(self, callback: types.CallbackQuery, data: str):
        """Обробляє запит на заглушення користувача"""
        try:
            parts = data.split(":")
            user_id_str, chat_id_str = parts[1], parts[2]
            user_id: int = int(user_id_str)
            chat_id: int = int(chat_id_str)
            
            await self.bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
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
                until_date=datetime.now() + timedelta(days=self.mute_duration_days)
            )
            
            await callback.answer(f"✅ Користувача заглушено на {self.mute_duration_days} днів")
            await callback.message.edit_text(
                callback.message.text + "\n\n🔇 **Користувача заглушено**",
                reply_markup=None,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback.answer(f"❌ Помилка: {e}")
    
    async def delete_reported_message(self, callback: types.CallbackQuery, data: str):
        """Обробляє запит на видалення повідомлення, на яке поскаржились"""
        try:
            parts = data.split(":")
            msg_id_str, chat_id_str = parts[1], parts[2]
            msg_id: int = int(msg_id_str)
            chat_id: int = int(chat_id_str)
            
            if msg_id in self.deleted_messages:
                # Спробуємо видалити повідомлення
                try:
                    await self.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    await callback.answer("✅ Повідомлення видалено")
                except Exception as e:
                    print(f"Error deleting reported message: {e}")
                    await callback.answer("❌ Не вдалось видалити повідомлення. Можливо, воно вже видалено.")
                
                # Оновлюємо повідомлення адміністратора
                await callback.message.edit_text(
                    callback.message.text + "\n\n❌ **Повідомлення видалено**",
                    reply_markup=None,
                    parse_mode="Markdown"
                )
            else:
                await callback.answer("❌ Повідомлення не знайдено в кеші")
        except Exception as e:
            await callback.answer(f"❌ Помилка: {e}")
    
    async def ignore_report(self, callback: types.CallbackQuery, data: str):
        """Обробляє запит на ігнорування скарги"""
        try:
            await callback.answer("✅ Скаргу проігноровано")
            await callback.message.edit_text(
                callback.message.text + "\n\n✓ **Скаргу проігноровано**",
                reply_markup=None,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback.answer(f"❌ Помилка: {e}")
    
    async def ban_user_from_callback(self, callback: types.CallbackQuery, data: str):
        try:
            parts = data.split(":")
            user_id_str, chat_id_str = parts[1], parts[2]
            user_id: int = int(user_id_str)
            chat_id: int = int(chat_id_str)
            await self.bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=datetime.now() + timedelta(days=self.ban_duration_days)
            )
            await callback.answer(f"✅ Користувача забанено на {self.ban_duration_days} днів")
            await callback.message.edit_text(
                callback.message.text + "\n\n🚫 **Користувача забанено**",
                reply_markup=None,
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback.answer(f"❌ Помилка: {e}")

    async def restore_message_from_callback(self, callback: types.CallbackQuery, data: str):
        try:
            parts = data.split(":")
            msg_id_str, chat_id_str = parts[1], parts[2]
            msg_id: int = int(msg_id_str)
            chat_id: int = int(chat_id_str)
            if msg_id in self.deleted_messages:
                msg_info = self.deleted_messages[msg_id]
                user_display = make_user_tag(types.User(
                    id=msg_info['user_id'],
                    is_bot=False,
                    first_name=msg_info.get('user_first_name', ''),
                    last_name=msg_info.get('user_last_name', ''),
                    username=msg_info.get('user_username', None),
                    language_code=None
                ))
                # Важливо: екранувати текст для Markdown!
                safe_text = (msg_info['text'] or "").replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
                restore_text = f"📝 **Повернене повідомлення від {user_display}:**\n{safe_text}"
                try:
                    chat_member = await self.bot.get_chat_member(chat_id, msg_info['user_id'])
                    if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                        await self.bot.restrict_chat_member(
                            chat_id=chat_id,
                            user_id=msg_info['user_id'],
                            permissions=types.ChatPermissions(
                                can_send_messages=True,
                                can_send_media_messages=True,
                                can_send_polls=True,
                                can_send_other_messages=True,
                                can_add_web_page_previews=True,
                                can_change_info=False,
                                can_invite_users=True,
                                can_pin_messages=False,
                                can_send_voice_notes = False,
                            ),
                        )
                except Exception as e:
                    print(e)
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=restore_text,
                        parse_mode="Markdown"
                    )
                    await callback.answer(f"✅ Повідомлення повернуто анонімно\n\n👤 Користувача {user_display} відновлено")
                    return
                except Exception as e:
                    print(f"Failed to send anonymously: {e}")
                    try:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=restore_text,
                            parse_mode="Markdown"
                        )
                        await callback.answer("✅ Повідомлення повернуто від імені бота")
                    except Exception as e2:
                        print(f"Failed to send as bot: {e2}")
                        await callback.answer("❌ Не вдалося повернути повідомлення")
                        return
                await callback.message.edit_text(
                    callback.message.text + "\n\n✅ **Повідомлення повернуто**",
                    reply_markup=None,
                    parse_mode="Markdown"
                )
            else:
                await callback.answer("❌ Повідомлення не знайдено")
        except Exception as e:
            await callback.answer(f"❌ Помилка: {e}")

    # async def restore_message_from_callback(self, callback: types.CallbackQuery, data: str):
    #     try:
    #         _, msg_id, chat_id = data.split(":")
    #         msg_id, chat_id = int(msg_id), int(chat_id)
    #         if msg_id in self.deleted_messages:
    #             msg_info = self.deleted_messages[msg_id]
    #             user_display = make_user_tag(types.User(
    #                 id=msg_info['user_id'],
    #                 is_bot=False,
    #                 first_name=msg_info.get('user_first_name', ''),
    #                 last_name=msg_info.get('user_last_name', ''),
    #                 username=msg_info.get('user_username', None),
    #                 language_code=None
    #             ))
    #             safe_text = (msg_info['text'] or "").replace('_', '\\_').replace('*', '\\*').replace('[',
    #                                                                                                  '\\[').replace(']',
    #                                                                                                                 '\\]')
    #             restore_text = f"📝 **Повернене повідомлення від {user_display}:**\n{safe_text}"
    #             try:
    #                 await self.bot.send_message(
    #                     chat_id=chat_id,
    #                     text=restore_text,
    #                     parse_mode="Markdown"
    #                 )
    #             except Exception as e:
    #                 print(f"Failed to send anonymously: {e}")
    #                 await callback.answer("❌ Не вдалося повернути повідомлення")
    #                 return
    #             await self.bot.restrict_chat_member(
    #                 chat_id=chat_id,
    #                 user_id=msg_info['user_id'],
    #                 permissions=types.ChatPermissions(
    #                     can_send_messages=True,
    #                     can_send_media_messages=True,
    #                     can_send_polls=True,
    #                     can_send_other_messages=True,
    #                     can_add_web_page_previews=True,
    #                     can_change_info=True,
    #                     can_invite_users=True,
    #                     can_pin_messages=True,
    #                 ),
    #             )
    #             await callback.answer(f"✅ Повідомлення повернуто\n👤 Користувача {user_display} відновлено")
    #             await callback.message.edit_text(
    #                 callback.message.text + "\n\n✅ **Повідомлення повернуто**",
    #                 parse_mode="Markdown"
    #             )
    #             return
    #         else:
    #             await callback.answer("❌ Повідомлення не знайдено")
    #     except Exception as e:
    #         await callback.answer(f"❌ Помилка: {e}")
    #         return

    async def add_chat_admins_callback(self, callback: types.CallbackQuery):
        try:
            chat_id = callback.message.chat.id
            chat_admins = await self.bot.get_chat_administrators(chat_id)
            added_count = 0
            for admin in chat_admins:
                if admin.user.id != self.bot.id:
                    if add_dynamic_admin(admin.user.id):
                        added_count += 1
            await callback.answer(f"✅ Додано {added_count} адміністраторів чату")
            self.admin_ids = ADMIN_IDS
        except Exception as e:
            await callback.answer(f"❌ Помилка: {e}")

    async def get_my_id(self, message: types.Message):
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        is_admin = self.is_admin(user_id)
        admin_status = "👑 **Адміністратор**" if is_admin else "👤 **Користувач**"
        await message.answer(
            f"🆔 **Ваш ID:** `{user_id}`\n"
            f"👤 **Ім'я:** {username}\n"
            f"📊 **Статус:** {admin_status}\n\n"
            f"💡 *Щоб додати себе як адміністратора, додайте ваш ID до ADMIN_IDS в .env файлі:*\n"
            f"`ADMIN_IDS={user_id}` або `ADMIN_IDS=123456789,{user_id}`",
            parse_mode="Markdown"
        )

    async def admin_management(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        env_admins = get_admin_ids()
        dynamic_admins = get_dynamic_admin_ids()
        env_text = "\n".join([f"• {admin_id} (з .env)" for admin_id in env_admins]) if env_admins else "Немає"
        dynamic_text = "\n".join(
            [f"• {admin_id} (динамічний)" for admin_id in dynamic_admins]) if dynamic_admins else "Немає"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати адміністратора", callback_data="add_admin_btn")],
            [InlineKeyboardButton(text="➖ Видалити адміністратора", callback_data="remove_admin_btn")],
            [InlineKeyboardButton(text="👥 Додати адміністраторів чату", callback_data="add_chat_admins")]
        ])
        await message.answer(
            f"👑 **Управління адміністраторами**\n\n"
            f"📋 **Адміністратори з .env:**\n{env_text}\n\n"
            f"📋 **Динамічні адміністратори:**\n{dynamic_text}\n\n"
            f"💡 *Адміністратори з .env не можна видаляти*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    async def admin_add_admin(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        await message.answer("🆔 Введіть ID користувача для додавання як адміністратора:")
        await state.set_state(AdminStates.waiting_for_admin_id_to_add)

    async def process_add_admin(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        try:
            admin_id = int(message.text.strip())
            if add_dynamic_admin(admin_id):
                self.admin_ids = get_all_admin_ids()
                await message.answer(f"✅ Користувача {admin_id} додано як адміністратора")
                print(f"✅ Updated admin list: {self.admin_ids}")
            else:
                await message.answer(f"❌ Користувач {admin_id} вже є адміністратором або не може бути доданий")
            await state.clear()
        except ValueError:
            await message.answer("❌ Невірний формат ID. Введіть число.")
            await state.clear()
        except Exception as e:
            await message.answer(f"❌ Помилка додавання адміністратора: {e}")
            await state.clear()

    async def admin_remove_admin(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        await message.answer("🆔 Введіть ID користувача для видалення з адміністраторів:")
        await state.set_state(AdminStates.waiting_for_admin_id_to_remove)

    async def process_remove_admin(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        try:
            admin_id = int(message.text.strip())
            if is_env_admin(admin_id):
                await message.answer(f"❌ Не можна видалити адміністратора {admin_id} (доданий через .env)")
            elif remove_dynamic_admin(admin_id):
                self.admin_ids = get_all_admin_ids()
                await message.answer(f"✅ Користувача {admin_id} видалено з адміністраторів")
                print(f"✅ Updated admin list: {self.admin_ids}")
            else:
                await message.answer(f"❌ Користувач {admin_id} не є адміністратором")
            await state.clear()
        except ValueError:
            await message.answer("❌ Невірний формат ID. Введіть число.")
            await state.clear()
        except Exception as e:
            await message.answer(f"❌ Помилка видалення адміністратора: {e}")
            await state.clear()

    async def admin_add_chat_admins(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        try:
            chat_id = message.chat.id
            chat_admins = await self.bot.get_chat_administrators(chat_id)
            added_count = 0
            for admin in chat_admins:
                if admin.user.id != self.bot.id:
                    if add_dynamic_admin(admin.user.id):
                        added_count += 1
            self.admin_ids = get_all_admin_ids()
            await message.answer(f"✅ Додано {added_count} адміністраторів чату до бота")
        except Exception as e:
            await message.answer(f"❌ Помилка додавання адміністраторів чату: {e}")

    async def admin_add_word(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        await message.answer("📝 Введіть слово або регулярний вираз для додавання до списку фільтрації:")
        await state.set_state(AdminStates.waiting_for_word_to_add)

    async def process_add_word(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        word = message.text.strip()
        if word.lower() == "назад":
            await self.admin_menu(message)
            await state.clear()
            return
        try:
            self.spam_filter.add_pattern(word)
            await message.answer(f"✅ Слово '{word}' додано до списку фільтрації")
            await message.answer("✅ Список фільтрації оновлено")
            await state.clear()
        except Exception as e:
            await message.answer(f"❌ Помилка додавання слова: {e}")
            await state.clear()

    async def admin_remove_word(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        await message.answer("🗑 Введіть слово для видалення зі списку фільтрації:")
        await state.set_state(AdminStates.waiting_for_word_to_remove)

    async def process_remove_word(self, message: types.Message, state: FSMContext):
        if not self.is_admin(message.from_user.id):
            return
        word = message.text.strip()
        try:
            removed = self.spam_filter.remove_pattern(word)
            if removed:
                await message.answer(f"✅ Слово '{word}' видалено зі списку фільтрації")
            else:
                await message.answer(f"❌ Слово '{word}' не знайдено в списку фільтрації")
            await state.clear()
        except Exception as e:
            await message.answer(f"❌ Помилка видалення слова: {e}")
            await state.clear()

    async def admin_list_words(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        patterns = self.spam_filter.get_patterns()
        if patterns:
            patterns_text = "\n".join([f"• {pattern}" for pattern in patterns])
            await message.answer(
                f"📋 **Список слів фільтрації:**\n\n{patterns_text}",
                parse_mode="Markdown"
            )
        else:
            await message.answer("📋 Список слів фільтрації порожній")
            
    async def show_char_map_menu(self, callback: types.CallbackQuery):
        """Показує меню управління картою символів"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Додати відповідність", callback_data="add_char_btn")],
            [InlineKeyboardButton(text="➖ Видалити відповідність", callback_data="remove_char_btn")],
            [InlineKeyboardButton(text="📋 Список відповідностей", callback_data="list_chars_btn")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_words")]
        ])
        await callback.message.edit_text(
            "🔤 **Управління відповідністю символів**\n\n"
            "Ця функція дозволяє створювати відповідність між символами, "
            "щоб бот міг знаходити спам навіть якщо використані замінники букв.\n\n"
            "Приклади:\n"
            "- Прості замінники: 'о' = 'o', 'а' = 'a', 'о' = '0'\n"
            "- Складні замінники: 'ы' = 'ьі', 'ю' = 'йу', 'щ' = 'shch'\n\n"
            "Оберіть дію:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    async def start_add_char(self, callback: types.CallbackQuery, state: FSMContext):
        """Запускає процес додавання відповідності символів"""
        await callback.message.edit_text(
            "➕ **Додавання відповідності символів**\n\n"
            "Введіть символ, який треба шукати (оригінал):\n\n"
            "💡 Для оригіналу можна використовувати лише один символ (наприклад, 'а').",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="char_map_btn")]
            ]),
            parse_mode="Markdown"
        )
        await state.set_state(AdminStates.waiting_for_char_to_add)
        
    async def process_add_char(self, message: types.Message, state: FSMContext):
        """Обробляє введення символу для додавання відповідності"""
        if not self.is_admin(message.from_user.id):
            return
            
        char = message.text.strip()
        if len(char) != 1:
            await message.answer("❌ Будь ласка, введіть лише один символ. Багатосимвольні комбінації підтримуються тільки для замінників, але не для оригіналів.")
            return
            
        await state.update_data(char_to_add=char)
        await message.answer(
            f"👍 Обрано символ: `{char}`\n\n"
            f"Тепер введіть символ-замінник або комбінацію символів (на що може бути замінено):",
            parse_mode="Markdown"
        )
        await state.set_state(AdminStates.waiting_for_mapping_to_add)
        
    async def process_add_mapping(self, message: types.Message, state: FSMContext):
        """Обробляє введення символу-замінника"""
        if not self.is_admin(message.from_user.id):
            return
            
        mapping = message.text.strip()
        if not mapping:
            await message.answer("❌ Будь ласка, введіть символ або комбінацію символів.")
            return
            
        data = await state.get_data()
        char = data.get("char_to_add")
        
        try:
            added = self.spam_filter.add_char_mapping(char, mapping)
            if added:
                await message.answer(
                    f"✅ Додано відповідність: `{char}` → `{mapping}`\n\n"
                    f"Тепер бот буде розпізнавати `{mapping}` як `{char}` при фільтрації.",
                    parse_mode="Markdown"
                )
            else:
                await message.answer(f"ℹ️ Відповідність `{char}` → `{mapping}` вже існує.", parse_mode="Markdown")
        except Exception as e:
            await message.answer(f"❌ Помилка додавання відповідності: {e}")
            
        await state.clear()
        
    async def start_remove_char(self, callback: types.CallbackQuery, state: FSMContext):
        """Запускає процес видалення відповідності символів"""
        await callback.message.edit_text(
            "➖ **Видалення відповідності символів**\n\n"
            "Введіть символ, для якого потрібно видалити відповідність (оригінал):",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="char_map_btn")]
            ]),
            parse_mode="Markdown"
        )
        await state.set_state(AdminStates.waiting_for_char_to_remove)
        
    async def process_remove_char(self, message: types.Message, state: FSMContext):
        """Обробляє введення символу для видалення відповідності"""
        if not self.is_admin(message.from_user.id):
            return
            
        char = message.text.strip()
        if len(char) != 1:
            await message.answer("❌ Будь ласка, введіть лише один символ.")
            return
            
        char_map = self.spam_filter.get_char_map()
        if char not in char_map or not char_map[char]:
            await message.answer(f"❌ Символ `{char}` не має відповідностей.", parse_mode="Markdown")
            await state.clear()
            return
            
        await state.update_data(char_to_remove=char)
        # Використовуємо більш безпечний вивід для багатосимвольних заміників
        mappings = ", ".join([f"`{m}`" for m in char_map[char]])
        
        await message.answer(
            f"👍 Знайдено відповідності для символу `{char}`: {mappings}\n\n"
            f"Тепер введіть символ або комбінацію символів-замінників, яку треба видалити:",
            parse_mode="Markdown"
        )
        await state.set_state(AdminStates.waiting_for_mapping_to_remove)
        
    async def process_remove_mapping(self, message: types.Message, state: FSMContext):
        """Обробляє введення символу-замінника для видалення"""
        if not self.is_admin(message.from_user.id):
            return
            
        mapping = message.text.strip()
        if not mapping:
            await message.answer("❌ Будь ласка, введіть символ або комбінацію символів.")
            return
            
        data = await state.get_data()
        char = data.get("char_to_remove")
        
        try:
            removed = self.spam_filter.remove_char_mapping(char, mapping)
            if removed:
                await message.answer(
                    f"✅ Видалено відповідність: `{char}` → `{mapping}`",
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    f"❌ Відповідність `{char}` → `{mapping}` не знайдена.",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await message.answer(f"❌ Помилка видалення відповідності: {e}")
            
        await state.clear()
        
    async def show_char_list(self, callback: types.CallbackQuery):
        """Показує список всіх відповідностей символів"""
        char_map = self.spam_filter.get_char_map()
        
        if not char_map:
            await callback.message.edit_text(
                "📋 **Список відповідностей символів**\n\n"
                "Словник відповідностей порожній.\n\n"
                "Додайте відповідності для покращення розпізнавання спаму.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="char_map_btn")]
                ]),
                parse_mode="Markdown"
            )
            return
            
        # Сортуємо символи за алфавітом
        chars = sorted(char_map.keys())
        
        text_parts = ["📋 **Список відповідностей символів**\n\n"]
        for char in chars:
            mappings = ", ".join(char_map[char])
            text_parts.append(f"`{char}` → {mappings}")
            
        # Об'єднуємо всі частини тексту з розділенням новим рядком
        text = "\n".join(text_parts)
        
        # Перевіряємо довжину тексту, щоб не перевищити ліміт Telegram
        if len(text) > 4000:
            text = text[:3900] + "\n\n... (список скорочено через обмеження Telegram)"
            
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="char_map_btn")]
            ]),
            parse_mode="Markdown"
        )