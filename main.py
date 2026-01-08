import asyncio
import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import db
from config import load_config
from orders import (
    handle_cancel_decision,
    handle_cancel_request,
    handle_new_order,
    handle_photo_delivery,
    handle_worker_action,
)
from pricing import handle_price
from routing import handle_addsource, handle_listsources


def _configure_logging() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def main() -> None:
    _configure_logging()
    config = load_config()
    asyncio.run(db.init_db(config["db_path"]))
    application = ApplicationBuilder().token(config["token"]).build()
    application.bot_data["db_path"] = config["db_path"]

    application.add_handler(
        CommandHandler("addsource", lambda u, c: handle_addsource(u, c, config["db_path"]))
    )
    application.add_handler(
        CommandHandler("listsources", lambda u, c: handle_listsources(u, c, config["db_path"]))
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.REPLY & filters.ChatType.GROUPS,
            handle_worker_action,
        )
    )
    application.add_handler(
        MessageHandler(
            filters.PHOTO & filters.REPLY & filters.ChatType.GROUPS,
            handle_photo_delivery,
        )
    )

    application.add_handler(
        MessageHandler(filters.TEXT & filters.REPLY, handle_cancel_request)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & filters.REPLY, handle_price)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_order)
    )

    application.add_handler(CallbackQueryHandler(handle_cancel_decision))

    application.run_polling()


if __name__ == "__main__":
    main()
