import re
import phonenumbers
import pycountry
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from config import config
from database import get_bot_status

COUNTRY_CACHE = {}

def get_country_info(country_code):
    if country_code in COUNTRY_CACHE:
        return COUNTRY_CACHE[country_code]
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        if country:
            flag = ''.join(chr(127397 + ord(c)) for c in country_code.upper())
            COUNTRY_CACHE[country_code] = (country.name, flag)
            return country.name, flag
    except:
        pass
    return "Unknown", "🏳️"

def extract_phone_numbers(text):
    potential = re.findall(r'\+?[\d\s\-\(\)]{8,20}', text)
    valid_numbers = set()
    for num in potential:
        cleaned = re.sub(r'[^\d+]', '', num)
        if len(cleaned) < 8:
            continue
        for test_num in [cleaned, '+' + cleaned.lstrip('+')]:
            try:
                parsed = phonenumbers.parse(test_num, None)
                if phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed):
                    valid_numbers.add(phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164))
                    break
            except:
                continue
    return list(valid_numbers)

def group_by_country(numbers):
    grouped = {}
    for num in numbers:
        try:
            parsed = phonenumbers.parse(num, None)
            region = phonenumbers.region_code_for_number(parsed)
            if region:
                country_name, flag = get_country_info(region)
                key = f"{flag} {country_name}"
                grouped.setdefault(key, []).append(num)
            else:
                grouped.setdefault("🏳️ Unknown", []).append(num)
        except:
            grouped.setdefault("🏳️ Unknown", []).append(num)
    return grouped

def format_numbers(numbers, with_plus=True):
    return numbers if with_plus else [num.lstrip('+') for num in numbers]

async def is_user_joined(client, user_id):
    try:
        for chat in [config.FORCE_JOIN_CHANNEL, config.FORCE_JOIN_GROUP]:
            member = await client.get_chat_member(chat, user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                return False
        return True
    except:
        return False

def force_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{config.FORCE_JOIN_CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton("👥 Join Group", url=f"https://t.me/{config.FORCE_JOIN_GROUP.lstrip('@')}")],
        [InlineKeyboardButton("✅ Verify", callback_data="verify_join")]
    ])

def main_menu_keyboard(user_id):
    buttons = [
        [InlineKeyboardButton("📁 My Files", callback_data="my_files")],
        [InlineKeyboardButton("👤 My Profile", callback_data="my_profile")]
    ]
    if user_id in config.ADMINS:
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def admin_panel_keyboard():
    status = "ON ✅" if get_bot_status() else "OFF ❌"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Bot Status: {status}", callback_data="toggle_bot")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ])

def format_selection_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ With + Format", callback_data="format_plus")],
        [InlineKeyboardButton("❌ Without + Format", callback_data="format_noplus")]
    ])
