import logging
from typing import Iterable, Optional

from telegram import Update
from telegram.ext import ContextTypes

import db
from utils import parse_price


def is_admin(user_id: int, admin_ids: Iterable[int]) -> bool:
    return user_id in admin_ids


def find_order_from_reply(update: Update) -> Optional[int]:
    if not update.effective_message or not update.effective_message.reply_to_message:
        return None
    reply = update.effective_message.reply_to_message
    # Try worker message lookup first.
    order = db.get_order_by_worker_message(update.effective_chat.id, reply.message_id)
    if order:
        return order["id"]
    order = db.get_order_by_customer_message(update.effective_chat.id, reply.message_id)
    if order:
        return order["id"]
    return None


async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_ids: set[int]):
    message = update.effective_message
    if not message or not message.from_user:
        return
    if not is_admin(message.from_user.id, admin_ids):
        return

    parsed = parse_price(message.text or "")
    if not parsed:
        return
    order_id = find_order_from_reply(update)
    if not order_id:
        await message.reply_text("Price must be set by replying to an order message.")
        return
    amount, currency = parsed
    db.set_price(order_id, amount, currency)
    logging.info("order_id=%s price=%s%s", order_id, amount, currency)
    await message.reply_text(f"Price recorded for order #{order_id}: {amount} {currency}")


async def handle_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_ids: set[int]):
    user = update.effective_user
    if not user or not is_admin(user.id, admin_ids):
        return
    totals = db.totals_by_currency()
    if not totals:
        await update.effective_message.reply_text("No prices recorded yet.")
        return
    lines = [f"{currency}: {total}" for currency, total in totals.items()]
    await update.effective_message.reply_text("Invoice summary:\n" + "\n".join(lines))
