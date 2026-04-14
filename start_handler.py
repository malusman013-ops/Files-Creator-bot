from pyrogram.types import Message
from helpers import is_user_joined, force_join_keyboard, main_menu_keyboard
from database import add_or_update_user, get_bot_status
from config import config

async def start_handler(client, message: Message):
    user = message.from_user
    if not get_bot_status() and user.id not in config.ADMINS:
        return await message.reply("⚠️ Bot is currently under maintenance. Please try again later.")

    add_or_update_user(user.id, user.username, user.first_name, user.last_name)

    if not await is_user_joined(client, user.id):
        await message.reply(
            "**🚫 Access Restricted**\n\nTo use this bot, you must join our channel and group first.",
            reply_markup=force_join_keyboard()
        )
        return
    await send_welcome(client, message)

async def send_welcome(client, message: Message):
    user = message.from_user
    text = f"""
**🎉 Welcome {user.first_name}!**

**📋 Your Details:**
👤 **First Name:** {user.first_name or 'N/A'}
👤 **Last Name:** {user.last_name or 'N/A'}
🔗 **Username:** @{user.username or 'N/A'}
🆔 **Telegram ID:** `{user.id}`

**🤖 About This Bot:**
This is a **File Creator Bot** for phone numbers. Send me any text containing phone numbers and I'll:
1️⃣ Extract all valid numbers
2️⃣ Detect countries automatically
3️⃣ Generate clean.txt files per country
4️⃣ Let you download them anytime

**⚡ Just send any text with numbers to start!**
"""
    await message.reply(text, reply_markup=main_menu_keyboard(user.id))
