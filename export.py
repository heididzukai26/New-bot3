import os
import tempfile
from typing import Optional

from openpyxl import Workbook
from telegram import Update
from telegram.ext import ContextTypes

import db
from pricing import is_admin


def build_workbook():
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"
    headers = ["ID", "Email", "Type", "Amount", "Status", "Price", "Currency", "Created", "Customer"]
    ws.append(headers)
    for order in db.all_orders():
        ws.append(
            [
                order["id"],
                order["email"],
                order["order_type"],
                order["cp_amount"],
                order["status"],
                order["price_amount"],
                order["price_currency"],
                order["created_at"],
                order["customer_name"],
            ]
        )
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2
    return wb


async def handle_export(update: Update, context: ContextTypes.DEFAULT_TYPE, admin_ids: set[int]):
    user = update.effective_user
    if not user or not is_admin(user.id, admin_ids):
        return
    wb = build_workbook()
    with tempfile.NamedTemporaryFile(delete=True, suffix=".xlsx") as tmp:
        wb.save(tmp.name)
        tmp.seek(0)
        await update.effective_message.reply_document(document=tmp, filename="orders.xlsx")
