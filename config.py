import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "7883953756"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000").rstrip("/")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///tournament.db")