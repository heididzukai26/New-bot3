import logging
from typing import Optional

import db


def register_source(chat_id: int, order_type: str, cp_amount: int) -> str:
    db.add_source(order_type, cp_amount, chat_id)
    logging.info("Registered source %s/%s -> %s", order_type, cp_amount, chat_id)
    return f"Source saved for {order_type} {cp_amount}"


def register_main(chat_id: int) -> str:
    db.set_main(chat_id)
    logging.info("Registered main group %s", chat_id)
    return "Main fallback group saved."


def pick_route(order_type: str, cp_amount: int) -> Optional[int]:
    direct = db.get_source(order_type, cp_amount)
    if direct:
        logging.info("Routing order type=%s amount=%s to worker %s", order_type, cp_amount, direct)
        return direct
    main = db.get_main()
    if main:
        logging.info("Routing order type=%s amount=%s to MAIN %s", order_type, cp_amount, main)
    else:
        logging.info("No route for type=%s amount=%s", order_type, cp_amount)
    return main


def list_sources_text() -> str:
    sources = db.list_sources()
    lines = [f"{order_type} {cp_amount} -> {chat_id}" for order_type, cp_amount, chat_id in sources]
    main = db.get_main()
    if main:
        lines.append(f"main -> {main}")
    return "\n".join(lines) if lines else "No sources configured."
