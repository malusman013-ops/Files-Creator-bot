import logging
import os
from pyrogram import Client, filters
from config import config
from database import init_db
from start_handler import start_handler
from callback_handler import callback_handler, number_handler, broadcast_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# پرانی session فائل ڈیلیٹ کرو
for file in ["file_creator_bot.session", "file_creator_bot.session-journal"]:
    if os.path.exists(file):
        os.remove(file)

app = Client(
    "file_creator_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    workers=2,
    sleep_threshold=180,
    max_concurrent_transmissions=1,
    in_memory=False
)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message): await start_handler(client, message)

@app.on_callback_query()
async def all_callbacks(client, callback): await callback_handler(client, callback)

@app.on_message(filters.private & filters.text & ~filters.command(["start", "cancel"]))
async def handle_text(client, message):
    if hasattr(client, 'broadcast_mode') and client.broadcast_mode.get(message.from_user.id):
        await broadcast_handler(client, message)
    else:
        await number_handler(client, message)

if __name__ == "__main__":
    init_db()
    app.run()
