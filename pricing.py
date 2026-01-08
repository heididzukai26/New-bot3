import logging
from telegram import Update
from telegram.ext import ContextTypes

import db
from utils import parse_price_amount


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text or not message.reply_to_message:
        return

    parsed = parse_price_amount(message.text)
    if not parsed:
        return

    db_path = context.application.bot_data["db_path"]
    record = await db.get_message_record(
        db_path, message.chat.id, message.reply_to_message.message_id
    )
    if not record:
        return

    amount, currency = parsed
    logging.info(
        "pricing order_id=%s amount=%s currency=%s",
        record["order_id"],
        amount,
        currency,
    )
    await message.reply_text(
        f"قیمت ثبت شد: {amount} {currency}\n"
        f"Pricing noted: {amount} {currency}"
    )
