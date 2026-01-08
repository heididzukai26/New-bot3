import logging
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

import db
from utils import (
    build_canonical_message,
    canonical_status,
    is_cancel_text,
    is_done_text,
    is_wrong_text,
    parse_order,
)


async def _react_safe(bot, chat_id: int, message_id: int, reaction: str) -> None:
    try:
        if hasattr(bot, "set_message_reaction"):
            await bot.set_message_reaction(
                chat_id=chat_id, message_id=message_id, reaction=reaction
            )
    except TelegramError:
        logging.exception("Failed to set reaction")


async def _edit_message_safe(bot, chat_id: int, message_id: int, text: str) -> None:
    try:
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
    except TelegramError:
        logging.exception("Failed to edit message")


async def _load_order(db_path: str, order_id: int) -> Optional[dict]:
    row = await db.get_order(db_path, order_id)
    return dict(row) if row else None


async def _update_canonical_messages(context: ContextTypes.DEFAULT_TYPE, db_path: str, order_id: int) -> None:
    order = await _load_order(db_path, order_id)
    if not order:
        return
    text = build_canonical_message(order)
    messages = await db.get_order_messages(db_path, order_id)
    for message in messages:
        await _edit_message_safe(
            context.bot, message["chat_id"], message["message_id"], text
        )
    if order["status"] == "completed":
        reaction = "✅"
    elif order["status"] in {"cancelled", "rejected"}:
        reaction = "👎"
    else:
        reaction = ""
    if reaction:
        for message in messages:
            await _react_safe(context.bot, message["chat_id"], message["message_id"], reaction)


async def handle_new_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text:
        return

    parsed = parse_order(message.text)
    if not parsed:
        return

    if not parsed.order_type:
        await message.reply_text(
            "لطفاً نوع سفارش را ارسال کنید (safe_fast / safe_slow / unsafe / fund).\n"
            "Please send the order type (safe_fast / safe_slow / unsafe / fund)."
        )
        return

    if parsed.cp_pack == 0:
        await message.reply_text(
            "لطفاً پک CP معتبر و تعداد را ارسال کنید (مثال: 10800x2).\n"
            "Please provide a valid CP pack and quantity (e.g., 10800x2)."
        )
        return

    if not parsed.password:
        await message.reply_text(
            "لطفاً رمز عبور اکانت را ارسال کنید.\n"
            "Please provide the account password."
        )
        return

    db_path = context.application.bot_data["db_path"]
    route = await db.get_route(db_path, parsed.order_type, parsed.cp_pack)
    if route is None:
        route = await db.get_main_route(db_path)
    if route is None:
        await message.reply_text(
            "در حال حاضر گروه پشتیبان موجود نیست. لطفاً بعداً تلاش کنید.\n"
            "No source group is available right now. Please try again later."
        )
        return

    order_id = await db.create_order(
        db_path=db_path,
        order_type=parsed.order_type,
        cp_pack=parsed.cp_pack,
        cp_qty=parsed.cp_qty,
        cp_total=parsed.cp_total,
        email=parsed.email,
        password=parsed.password,
        ign=parsed.ign,
    )
    order = await _load_order(db_path, order_id)
    if not order:
        return
    canonical = build_canonical_message(order)
    customer_message = await message.reply_text(canonical)
    await db.set_order_message(
        db_path, order_id, "customer", message.chat.id, customer_message.message_id
    )
    source_message = await context.bot.send_message(chat_id=route, text=canonical)
    await db.set_order_message(
        db_path, order_id, "source", route, source_message.message_id
    )
    logging.info("order_id=%s status=%s", order_id, order["status"])


async def handle_worker_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.reply_to_message:
        return
    if not message.text:
        return
    if not (is_done_text(message.text) or is_wrong_text(message.text)):
        return

    db_path = context.application.bot_data["db_path"]
    record = await db.get_message_record(
        db_path, message.chat.id, message.reply_to_message.message_id
    )
    if not record or record["role"] != "source":
        return

    order_id = record["order_id"]
    order = await _load_order(db_path, order_id)
    if not order:
        return

    if is_done_text(message.text):
        if order["status"] == "cancelled":
            await message.reply_text("Order is cancelled; delivery rejected.")
            return
        if order["status"] != "pending":
            await message.reply_text(
                f"Order status is {canonical_status(order['status'])[0]}."
            )
            return
        updated = await db.update_order_status(
            db_path,
            order_id,
            "pending",
            "completed",
            actor_field="completed_by",
            actor_id=message.from_user.id if message.from_user else None,
            timestamp_field="completed_at",
        )
        if not updated:
            await message.reply_text("Order already reviewed.")
            return
        logging.info("order_id=%s status=completed", order_id)
        await _update_canonical_messages(context, db_path, order_id)
        return

    if order["status"] == "cancelled":
        await message.reply_text("Order is cancelled; rejection not needed.")
        return
    if order["status"] != "pending":
        await message.reply_text(
            f"Order status is {canonical_status(order['status'])[0]}."
        )
        return
    updated = await db.update_order_status(
        db_path,
        order_id,
        "pending",
        "rejected",
        actor_field="rejected_by",
        actor_id=message.from_user.id if message.from_user else None,
    )
    if not updated:
        await message.reply_text("Order already reviewed.")
        return
    logging.info("order_id=%s status=rejected", order_id)
    await _update_canonical_messages(context, db_path, order_id)


async def handle_photo_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.photo or not message.reply_to_message:
        return
    caption = message.caption or ""
    if "done" not in caption.lower():
        return
    db_path = context.application.bot_data["db_path"]
    record = await db.get_message_record(
        db_path, message.chat.id, message.reply_to_message.message_id
    )
    if not record or record["role"] != "source":
        return
    order = await _load_order(db_path, record["order_id"])
    if not order:
        return
    if order["status"] == "cancelled":
        await message.reply_text("Order is cancelled; delivery rejected.")
        return
    if order["status"] != "pending":
        await message.reply_text(
            f"Order status is {canonical_status(order['status'])[0]}."
        )
        return
    updated = await db.update_order_status(
        db_path,
        order["id"],
        "pending",
        "completed",
        actor_field="completed_by",
        actor_id=message.from_user.id if message.from_user else None,
        timestamp_field="completed_at",
    )
    if not updated:
        await message.reply_text("Order already reviewed.")
        return
    logging.info("order_id=%s status=completed (photo)", order["id"])
    await _update_canonical_messages(context, db_path, order["id"])


async def handle_cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.reply_to_message or not message.text:
        return
    if not is_cancel_text(message.text):
        return

    db_path = context.application.bot_data["db_path"]
    record = await db.get_message_record(
        db_path, message.chat.id, message.reply_to_message.message_id
    )
    if not record or record["role"] != "customer":
        return
    order = await _load_order(db_path, record["order_id"])
    if not order:
        return
    if order["status"] == "completed":
        await message.reply_text(
            "سفارش قبلاً تکمیل شده و قابل لغو نیست.\n"
            "The order is already completed and cannot be cancelled."
        )
        return
    if order["status"] == "cancelled":
        await message.reply_text(
            "سفارش قبلاً لغو شده است.\n"
            "The order is already cancelled."
        )
        return
    if order["status"] == "rejected":
        await message.reply_text(
            "سفارش رد شده و قابل لغو نیست.\n"
            "The order was rejected and cannot be cancelled."
        )
        return
    if order["status"] == "pending_cancel":
        await message.reply_text(
            "درخواست لغو قبلاً ارسال شده است.\n"
            "A cancel request is already pending."
        )
        return

    updated = await db.update_order_status(db_path, order["id"], "pending", "pending_cancel")
    if not updated:
        await message.reply_text(
            "درخواست لغو ثبت نشد. لطفاً دوباره تلاش کنید.\n"
            "Cancel request could not be registered. Please try again."
        )
        return

    source_message = await db.get_message_record_for_role(db_path, order["id"], "source")
    if not source_message:
        await message.reply_text(
            "این سفارش به گروه منبع ارسال نشده است.\n"
            "This order has not been routed to a source group."
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Approve", callback_data=f"cancel:{order['id']}:approve"),
                InlineKeyboardButton("Reject", callback_data=f"cancel:{order['id']}:reject"),
            ]
        ]
    )
    request_message = await context.bot.send_message(
        chat_id=source_message["chat_id"],
        reply_to_message_id=source_message["message_id"],
        text=f"Cancel request for Order #{order['id']}",
        reply_markup=keyboard,
    )
    await db.create_cancel_request(
        db_path,
        order["id"],
        source_message["chat_id"],
        source_message["message_id"],
        request_message.message_id,
    )
    logging.info("order_id=%s status=pending_cancel", order["id"])
    await _update_canonical_messages(context, db_path, order["id"])
    await message.reply_text(
        "درخواست لغو برای تیم ارسال شد. به‌زودی اطلاع می‌دهیم.\n"
        "Cancel request sent to the team. We will update you shortly."
    )


async def handle_cancel_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return
    if not query.data.startswith("cancel:"):
        return
    await query.answer()
    _, order_id_str, decision = query.data.split(":")
    order_id = int(order_id_str)
    db_path = context.application.bot_data["db_path"]

    request = await db.get_cancel_request(db_path, order_id)
    if not request:
        await query.edit_message_text("Cancel request not found.")
        return
    if request["status"] != "pending":
        await query.edit_message_text("Cancel request already decided.")
        return

    if decision == "approve":
        updated = await db.update_order_status(
            db_path,
            order_id,
            "pending_cancel",
            "cancelled",
            actor_field="cancelled_by",
            actor_id=query.from_user.id if query.from_user else None,
        )
        if not updated:
            await query.edit_message_text("Order already reviewed.")
            return
        await db.update_cancel_request_status(db_path, order_id, "approved", query.from_user.id)
        logging.info("order_id=%s status=cancelled", order_id)
        await _update_canonical_messages(context, db_path, order_id)
        await query.edit_message_text(f"Order #{order_id} cancelled.")
        return

    if decision == "reject":
        updated = await db.update_order_status(db_path, order_id, "pending_cancel", "pending")
        if not updated:
            await query.edit_message_text("Order already reviewed.")
            return
        await db.update_cancel_request_status(db_path, order_id, "rejected", query.from_user.id)
        logging.info("order_id=%s status=pending", order_id)
        await _update_canonical_messages(context, db_path, order_id)
        await query.edit_message_text(f"Cancel request rejected for Order #{order_id}.")
        return
