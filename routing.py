from telegram import Update
from telegram.ext import ContextTypes

import db
from utils import VALID_PACKS, normalize_type


async def handle_addsource(update: Update, context: ContextTypes.DEFAULT_TYPE, db_path: str) -> None:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if not message or not chat:
        return
    if not args:
        await message.reply_text("Usage: /addsource <type> <pack> or /addsource main")
        return
    if args[0].lower() == "main":
        await db.set_route(db_path, "main", None, chat.id)
        await message.reply_text("Main route set for this group.")
        return
    if len(args) < 2:
        await message.reply_text("Usage: /addsource <type> <pack>")
        return
    order_type = normalize_type(args[0]) or args[0].lower()
    try:
        pack = int(args[1])
    except ValueError:
        await message.reply_text("Pack must be a number.")
        return
    if pack not in VALID_PACKS:
        await message.reply_text("Invalid CP pack. Allowed: 80, 420, 880, 2400, 5000, 10800")
        return
    await db.set_route(db_path, order_type, pack, chat.id)
    await message.reply_text(f"Route saved for {order_type} {pack}.")


async def handle_listsources(update: Update, context: ContextTypes.DEFAULT_TYPE, db_path: str) -> None:
    message = update.effective_message
    if not message:
        return
    routes = await db.list_routes(db_path)
    if not routes:
        await message.reply_text("No routes configured.")
        return
    lines = []
    for route in routes:
        if route["type"] == "main":
            lines.append(f"main -> {route['chat_id']}")
        else:
            lines.append(f"{route['type']} {route['cp_pack']} -> {route['chat_id']}")
    await message.reply_text("\n".join(lines))
