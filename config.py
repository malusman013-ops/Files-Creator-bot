import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL", "@your_channel")
    FORCE_JOIN_GROUP = os.getenv("FORCE_JOIN_GROUP", "@your_group")

    ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]

    DB_NAME = "bot_database.db"
    BOT_ACTIVE = True
    WORKERS = int(os.getenv("WORKERS", "2"))

config = Config()
