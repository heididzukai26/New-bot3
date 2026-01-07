import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db
from export import handle_export
from orders import (
    handle_cancel_decision,
    handle_cancel_request,
    handle_new_order,
    handle_worker_done,
    handle_worker_wrong,
)
from pricing import handle_invoice, handle_price
from routing import list_sources_text, register_main, register_source
from utils import largest_number


def load_admin_ids() -> set[int]:
    ids = os.getenv("ADMIN_IDS", "")
    result = set()
    for part in ids.split(","):
        part = part.strip()
        if part.isdigit():
            result.add(int(part))
    return result


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send your order details. Please include email and amount.")


async def addsource(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /addsource <type> <amount> or /addsource main")
        return
    if args[0].lower() == "main":
        msg = register_main(chat.id)
        await update.message.reply_text(msg)
        return
    if len(args) < 2:
        await update.message.reply_text("Usage: /addsource <type> <amount>")
        return
    order_type = args[0].lower()
    cp_amount = largest_number(args[1])
    if cp_amount is None:
        await update.message.reply_text("Amount missing or invalid.")
        return
    msg = register_source(chat.id, order_type, cp_amount)
    await update.message.reply_text(msg)


async def listsources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(list_sources_text())


def main():
    load_dotenv()
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    db.init_db()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")

    admin_ids = load_admin_ids()
    application = ApplicationBuilder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addsource", addsource))
    application.add_handler(CommandHandler("listsources", listsources))
    application.add_handler(CommandHandler("invoice", lambda u, c: handle_invoice(u, c, admin_ids)))
    application.add_handler(CommandHandler("export", lambda u, c: handle_export(u, c, admin_ids)))

    # Worker actions
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.ChatType.GROUPS
            & filters.REPLY
            & filters.Regex(r"(?i)^done$"),
            handle_worker_done,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.ChatType.GROUPS
            & filters.REPLY
            & filters.Regex(r"(?i)^wrong$"),
            handle_worker_wrong,
        )
    )

    # Pricing by admins
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & filters.REPLY
            & filters.User(user_id=admin_ids)
            & filters.Regex(r"(?i)(\d[\d,]*)(\$|tm)"),
            lambda u, c: handle_price(u, c, admin_ids),
        )
    )

    # Cancel requests from customers
    application.add_handler(
        MessageHandler(filters.TEXT & filters.REPLY, handle_cancel_request)
    )

    # Core order intake
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_order))

    application.add_handler(CallbackQueryHandler(handle_cancel_decision))

    application.run_polling()


if __name__ == "__main__":
    main()
