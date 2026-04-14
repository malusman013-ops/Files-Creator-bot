import time
import os
import asyncio
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from helpers import is_user_joined, main_menu_keyboard, admin_panel_keyboard, group_by_country, format_numbers, extract_phone_numbers, format_selection_keyboard
from database import get_user, get_user_files, get_bot_status, set_bot_status, get_total_users, get_active_users, get_all_users, update_last_active, save_file_record
from start_handler import send_welcome
from datetime import datetime
from config import config

USER_SESSIONS = {}

async def callback_handler(client, callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id

    if data == "verify_join":
        if await is_user_joined(client, user_id):
            await callback.message.delete()
            await send_welcome(client, callback.message)
        else:
            await callback.answer("❌ You haven't joined both channel and group yet!", show_alert=True)

    elif data == "my_profile":
        user_data = get_user(user_id)
        if user_data:
            _, username, first_name, last_name, join_date, last_active = user_data
            join_dt = datetime.fromtimestamp(join_date).strftime("%Y-%m-%d %H:%M")
            total_time = int(time.time()) - join_date
            days, rem = divmod(total_time, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, _ = divmod(rem, 60)
            text = f"""
**👤 My Profile**

🆔 **User ID:** `{user_id}`
🔗 **Username:** @{username or 'N/A'}
👤 **First Name:** {first_name or 'N/A'}
👤 **Last Name:** {last_name or 'N/A'}
📅 **Join Date:** {join_dt}
⏱ **Total Time:** {days}d {hours}h {minutes}m
"""
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
            ]))

    elif data == "my_files":
        files = get_user_files(user_id)
        if not files:
            return await callback.answer("📂 You haven't generated any files yet!", show_alert=True)
        buttons = []
        for fid, country, total, fmt, file_name, created in files[:10]:
            dt = datetime.fromtimestamp(created).strftime("%m/%d")
            buttons.append([InlineKeyboardButton(
                f"{country} - {total} nums - {fmt} - {dt}",
                callback_data=f"getfile_{fid}"
            )])
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
        await callback.message.edit_text("**📁 Your Generated Files:**", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("getfile_"):
        fid = int(data.split("_")[1])
        files = get_user_files(user_id)
        file_info = next((f for f in files if f[0] == fid), None)
        if file_info and os.path.exists(file_info[4]):
            try:
                await client.send_document(user_id, file_info[4])
                await callback.answer("✅ File sent!")
            except:
                await callback.answer("❌ Error sending file", show_alert=True)
        else:
            await callback.answer("❌ File not found", show_alert=True)

    elif data == "back_main":
        await callback.message.edit_text("**🏠 Main Menu**\n\nSelect an option below:", reply_markup=main_menu_keyboard(user_id))

    elif data == "admin_panel":
        if user_id not in config.ADMINS:
            return await callback.answer("❌ Access denied", show_alert=True)
        await callback.message.edit_text("**⚙️ Admin Panel**", reply_markup=admin_panel_keyboard())

    elif data == "toggle_bot":
        if user_id not in config.ADMINS:
            return await callback.answer("❌ Access denied", show_alert=True)
        new_status = not get_bot_status()
        set_bot_status(new_status)
        await callback.message.edit_text("**⚙️ Admin Panel**", reply_markup=admin_panel_keyboard())
        await callback.answer(f"Bot is now {'ON' if new_status else 'OFF'}")

    elif data == "bot_stats":
        if user_id not in config.ADMINS:
            return await callback.answer("❌ Access denied", show_alert=True)
        total = get_total_users()
        active_24h = get_active_users(1)
        active_7d = get_active_users(7)
        text = f"""
**📊 Bot Statistics**

👥 **Total Users:** {total}
🟢 **Active 24h:** {active_24h}
📈 **Active 7d:** {active_7d}
🤖 **Bot Status:** {'ON ✅' if get_bot_status() else 'OFF ❌'}
"""
        await callback.answer(text, show_alert=True)

    elif data == "broadcast":
        if user_id not in config.ADMINS:
            return await callback.answer("❌ Access denied", show_alert=True)
        await callback.message.reply("**📢 Send the message you want to broadcast to all users.\n\nUse /cancel to abort.**")
        client.broadcast_mode = {user_id: True}

    elif data in ["format_plus", "format_noplus"]:
        if user_id not in USER_SESSIONS:
            return await callback.answer("❌ Session expired. Send numbers again.", show_alert=True)
        with_plus = data == "format_plus"
        grouped = USER_SESSIONS[user_id]
        await callback.message.edit_text("⚙️ **Generating files...**")
        sent_files = 0
        for country, numbers in grouped.items():
            clean_country = country.split(' ', 1)[1] if ' ' in country else country
            clean_country = clean_country.replace(' ', '_')
            formatted_nums = format_numbers(numbers, with_plus)
            filename = f"{clean_country}.{len(numbers)}_numbers.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(formatted_nums))
            fmt_type = "with_plus" if with_plus else "without_plus"
            save_file_record(user_id, country, len(numbers), fmt_type, filename)
            try:
                await client.send_document(user_id, filename, caption=f"{country} - {len(numbers)} numbers")
                sent_files += 1
            except Exception as e:
                print(f"Error sending file: {e}")
        del USER_SESSIONS[user_id]
        await callback.message.delete()
        await client.send_message(user_id, f"✅ **Done!** Generated and sent {sent_files} file(s). Check '📁 My Files' to re-download anytime.")

    await callback.answer()

async def number_handler(client, message: Message):
    user_id = message.from_user.id
    if not get_bot_status() and user_id not in config.ADMINS:
        return await message.reply("⚠️ Bot is currently under maintenance.")
    update_last_active(user_id)
    if not message.text:
        return await message.reply("❌ Please send text containing phone numbers.")
    numbers = extract_phone_numbers(message.text)
    if not numbers:
        return await message.reply("❌ No valid phone numbers detected in your text.")
    grouped = group_by_country(numbers)
    USER_SESSIONS[user_id] = grouped
    text = "**📊 Detection Results:**\n\n"
    total = 0
    for country, nums in grouped.items():
        text += f"• {country} – **{len(nums)}** numbers detected\n"
        total += len(nums)
    text += f"\n**Total: {total} unique numbers**\n\nSelect output format:"
    await message.reply(text, reply_markup=format_selection_keyboard())

async def broadcast_handler(client, message: Message):
    admin_id = message.from_user.id
    if admin_id not in config.ADMINS:
        return
    if not hasattr(client, 'broadcast_mode') or not client.broadcast_mode.get(admin_id):
        return
    if message.text == "/cancel":
        client.broadcast_mode[admin_id] = False
        return await message.reply("❌ Broadcast cancelled.")
    client.broadcast_mode[admin_id] = False
    users = get_all_users()
    success, failed = 0, 0
    status_msg = await message.reply(f"📢 Broadcasting to {len(users)} users...")
    for user_id in users:
        try:
            await message.copy(user_id)
            success += 1
        except:
            failed += 1
        await asyncio.sleep(0.05)
    await status_msg.edit(f"**📢 Broadcast Complete**\n\n✅ Success: {success}\n❌ Failed: {failed}")
