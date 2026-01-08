import os

from dotenv import load_dotenv


def load_config() -> dict:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    admin_ids: set[int] = set()
    for part in admin_ids_raw.split(","):
        part = part.strip()
        if part.isdigit():
            admin_ids.add(int(part))
    db_path = os.getenv("DB_PATH", "bot.db")
    return {"token": token, "admin_ids": admin_ids, "db_path": db_path}
