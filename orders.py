import logging
from typing import Iterable, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.constants import ChatType
from telegram.error import TelegramError
from telegram.ext import ContextTypes

import db
from routing import pick_route
from utils import extract_email, is_order_message, largest_number, parse_order_type


CANCEL_KEYWORDS = {"cancel", "کنسل", "لغو"}


async def _react_safe(bot, chat_id: int, message_id: int, reaction: str):
    try:
        if hasattr(bot, "set_message_reaction"):
            await bot.set_message_reaction(chat_id=chat_id, message_id=message_id, reaction=reaction)
    except TelegramError as exc:  # pragma: no cover
        logging.warning("Failed to set reaction: %s", exc)


async def handle_new_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message: Message = update.effective_message
    chat = update.effective_chat

    # Ignore stray messages from worker/main groups unless replying.
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) and not message.reply_to_message:
        return

    text = message.text or ""
    if not is_order_message(text):
        return

    email = extract_email(text) or ""
    cp_amount = largest_number(text)
    if cp_amount is None:
        await message.reply_text("Could not detect amount in your order.")
        return

    order_type = parse_order_type(text)
    destination = pick_route(order_type, cp_amount)
    if destination is None:
        await message.reply_text("No worker available right now. Please wait for instructions.")
        return

    order_id = db.create_order(
        customer_chat_id=chat.id,
        customer_message_id=message.message_id,
        customer_name=message.from_user.full_name if message.from_user else "",
        email=email,
        order_text=text,
        order_type=order_type,
        cp_amount=cp_amount,
        routed_group_id=destination,
    )
    worker_text = (
        f"Order #{order_id}\n"
        f"Type: {order_type}\n"
        f"Amount: {cp_amount}\n"
        f"Email: {email}\n"
        f"Customer: {message.from_user.full_name if message.from_user else 'customer'}\n\n"
        f"{text}"
    )
    worker_message = await context.bot.send_message(chat_id=destination, text=worker_text)
    db.set_worker_message(order_id, destination, worker_message.message_id)
    logging.info(
        "order_id=%s type=%s cp_amount=%s routed_group=%s status=routed",
        order_id,
        order_type,
        cp_amount,
        destination,
    )
    await message.reply_text(f"Order received. ID: #{order_id}. We will update you soon.")


async def handle_worker_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    if message.reply_to_message is None:
        return
    order = db.get_order_by_worker_message(chat.id, message.reply_to_message.message_id)
    if not order:
        return
    if order["status"] in ("cancelled", "cancel_requested"):
        await message.reply_text("Order is pending cancel; delivery skipped.")
        return

    db.update_status(order["id"], "done")
    logging.info("order_id=%s status=done", order["id"])
    await _react_safe(context.bot, chat.id, order["worker_message_id"], "✅")
    await context.bot.send_message(
        chat_id=order["customer_chat_id"],
        reply_to_message_id=order["customer_message_id"],
        text="Your order has been delivered. Thank you!",
    )


async def handle_worker_wrong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    if message.reply_to_message is None:
        return
    order = db.get_order_by_worker_message(chat.id, message.reply_to_message.message_id)
    if not order:
        return
    db.update_status(order["id"], "rejected")
    logging.info("order_id=%s status=rejected", order["id"])
    await _react_safe(context.bot, chat.id, order["worker_message_id"], "👎")
    await _react_safe(context.bot, order["customer_chat_id"], order["customer_message_id"], "👎")
    await context.bot.send_message(
        chat_id=order["customer_chat_id"],
        reply_to_message_id=order["customer_message_id"],
        text="Your order was rejected. Please contact support.",
    )


async def handle_cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message:
        return
    if not message.text:
        return
    if not any(word in message.text.lower() for word in CANCEL_KEYWORDS):
        return
    order = db.get_order_by_customer_message(message.chat.id, message.reply_to_message.message_id)
    if not order:
        await message.reply_text("Could not find the order you are trying to cancel.")
        return
    if order["status"] == "cancelled":
        await message.reply_text("Order already cancelled.")
        return
    if order["status"] == "done":
        await message.reply_text("Order already completed and cannot be cancelled.")
        return
    if order["worker_chat_id"] is None or order["worker_message_id"] is None:
        await message.reply_text("This order was not routed yet.")
        return
    db.update_status(order["id"], "cancel_requested")
    logging.info("order_id=%s status=cancel_requested", order["id"])
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Approve", callback_data=f"cancel:{order['id']}:approve"),
                InlineKeyboardButton("Reject", callback_data=f"cancel:{order['id']}:reject"),
            ]
        ]
    )
    await context.bot.send_message(
        chat_id=order["worker_chat_id"],
        reply_to_message_id=order["worker_message_id"],
        text=f"Cancel request for order #{order['id']}.",
        reply_markup=keyboard,
    )
    await message.reply_text("Cancel request sent to the worker. We will notify you.")


async def handle_cancel_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    if not query.data.startswith("cancel:"):
        return
    await query.answer()
    _, order_id, decision = query.data.split(":")
    order = db.get_order(int(order_id))
    if not order:
        await query.edit_message_text("Order not found.")
        return

    if decision == "approve":
        db.update_status(order["id"], "cancelled")
        logging.info("order_id=%s status=cancelled", order["id"])
        await _react_safe(context.bot, order["worker_chat_id"], order["worker_message_id"], "👎")
        await _react_safe(context.bot, order["customer_chat_id"], order["customer_message_id"], "👎")
        await context.bot.send_message(
            chat_id=order["customer_chat_id"],
            reply_to_message_id=order["customer_message_id"],
            text="Your cancel request was approved. Order cancelled.",
        )
        await query.edit_message_text(f"Order #{order_id} cancelled.")
    else:
        db.update_status(order["id"], "routed")
        logging.info("order_id=%s status=cancel_rejected", order["id"])
        await context.bot.send_message(
            chat_id=order["customer_chat_id"],
            reply_to_message_id=order["customer_message_id"],
            text="Cancel request was rejected. Your order is still in progress.",
        )
        await query.edit_message_text(f"Order #{order_id} cancel rejected.")


def is_worker_done_text(text: str) -> bool:
    return text.lower().strip() == "done"


def is_worker_wrong_text(text: str) -> bool:
    return text.lower().strip() == "wrong"
