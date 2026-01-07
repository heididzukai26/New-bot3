import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple


def get_connection() -> sqlite3.Connection:
    db_path = os.getenv("DATABASE_PATH", "bot.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_chat_id INTEGER,
                customer_message_id INTEGER,
                customer_name TEXT,
                email TEXT,
                order_text TEXT,
                order_type TEXT,
                cp_amount INTEGER,
                routed_group_id INTEGER,
                worker_chat_id INTEGER,
                worker_message_id INTEGER,
                status TEXT,
                price_amount REAL,
                price_currency TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                order_type TEXT,
                cp_amount INTEGER,
                chat_id INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (order_type, cp_amount)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )


def add_source(order_type: str, cp_amount: int, chat_id: int):
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO sources(order_type, cp_amount, chat_id, updated_at)
            VALUES(?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(order_type, cp_amount) DO UPDATE SET
                chat_id=excluded.chat_id,
                updated_at=excluded.updated_at
            """,
            (order_type, cp_amount, chat_id),
        )


def set_main(chat_id: int):
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO settings(key, value) VALUES('main_chat', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (str(chat_id),),
        )


def get_main() -> Optional[int]:
    with db_cursor() as cur:
        cur.execute("SELECT value FROM settings WHERE key='main_chat'")
        row = cur.fetchone()
        return int(row["value"]) if row else None


def list_sources() -> List[Tuple[str, int, int]]:
    with db_cursor() as cur:
        cur.execute("SELECT order_type, cp_amount, chat_id, updated_at FROM sources ORDER BY updated_at DESC")
        return [(row["order_type"], row["cp_amount"], row["chat_id"]) for row in cur.fetchall()]


def get_source(order_type: str, cp_amount: int) -> Optional[int]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT chat_id FROM sources WHERE order_type=? AND cp_amount=?",
            (order_type, cp_amount),
        )
        row = cur.fetchone()
        return row["chat_id"] if row else None


def create_order(
    customer_chat_id: int,
    customer_message_id: int,
    customer_name: str,
    email: str,
    order_text: str,
    order_type: str,
    cp_amount: int,
    routed_group_id: Optional[int],
) -> int:
    with db_cursor() as cur:
        cur.execute(
            """
            INSERT INTO orders(
                customer_chat_id,
                customer_message_id,
                customer_name,
                email,
                order_text,
                order_type,
                cp_amount,
                routed_group_id,
                status
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, 'routed')
            """,
            (
                customer_chat_id,
                customer_message_id,
                customer_name,
                email,
                order_text,
                order_type,
                cp_amount,
                routed_group_id,
            ),
        )
        return cur.lastrowid


def set_worker_message(order_id: int, chat_id: int, message_id: int):
    with db_cursor() as cur:
        cur.execute(
            """
            UPDATE orders SET worker_chat_id=?, worker_message_id=? WHERE id=?
            """,
            (chat_id, message_id, order_id),
        )


def update_status(order_id: int, status: str):
    with db_cursor() as cur:
        cur.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))


def set_price(order_id: int, amount: float, currency: str):
    with db_cursor() as cur:
        cur.execute(
            "UPDATE orders SET price_amount=?, price_currency=? WHERE id=?",
            (amount, currency, order_id),
        )


def get_order_by_worker_message(chat_id: int, message_id: int) -> Optional[sqlite3.Row]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM orders WHERE worker_chat_id=? AND worker_message_id=?
            """,
            (chat_id, message_id),
        )
        return cur.fetchone()


def get_order_by_customer_message(chat_id: int, message_id: int) -> Optional[sqlite3.Row]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT * FROM orders WHERE customer_chat_id=? AND customer_message_id=?
            """,
            (chat_id, message_id),
        )
        return cur.fetchone()


def get_order(order_id: int) -> Optional[sqlite3.Row]:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        return cur.fetchone()


def all_orders() -> List[Dict[str, Any]]:
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, email, order_type, cp_amount, status, price_amount, price_currency, created_at, customer_name FROM orders ORDER BY id ASC"
        )
        return [dict(row) for row in cur.fetchall()]


def totals_by_currency() -> Dict[str, float]:
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT price_currency, SUM(price_amount) as total
            FROM orders
            WHERE price_amount IS NOT NULL
            GROUP BY price_currency
            """
        )
        return {row["price_currency"]: row["total"] for row in cur.fetchall()}
