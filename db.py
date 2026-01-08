import aiosqlite

from typing import Optional


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                type TEXT NOT NULL,
                cp_pack INTEGER NOT NULL,
                cp_qty INTEGER NOT NULL,
                cp_total INTEGER NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                ign TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                completed_by INTEGER,
                cancelled_by INTEGER,
                rejected_by INTEGER
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS order_messages (
                order_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                PRIMARY KEY (order_id, role),
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_order_messages_chat
            ON order_messages(chat_id, message_id)
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                cp_pack INTEGER,
                chat_id INTEGER NOT NULL,
                UNIQUE (type, cp_pack)
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS cancel_requests (
                order_id INTEGER NOT NULL,
                worker_chat_id INTEGER NOT NULL,
                worker_message_id INTEGER NOT NULL,
                request_message_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                decided_by INTEGER,
                decided_at TEXT,
                PRIMARY KEY (order_id),
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_orders_status
            ON orders(status)
            """
        )
        await db.commit()


async def create_order(
    db_path: str,
    order_type: str,
    cp_pack: int,
    cp_qty: int,
    cp_total: int,
    email: str,
    password: str,
    ign: Optional[str],
) -> int:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        cursor = await db.execute(
            """
            INSERT INTO orders(
                status,
                type,
                cp_pack,
                cp_qty,
                cp_total,
                email,
                password,
                ign
            ) VALUES('pending', ?, ?, ?, ?, ?, ?, ?)
            """,
            (order_type, cp_pack, cp_qty, cp_total, email, password, ign),
        )
        await db.commit()
        return cursor.lastrowid


async def set_order_message(
    db_path: str, order_id: int, role: str, chat_id: int, message_id: int
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO order_messages(order_id, role, chat_id, message_id)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(order_id, role) DO UPDATE SET
                chat_id=excluded.chat_id,
                message_id=excluded.message_id
            """,
            (order_id, role, chat_id, message_id),
        )
        await db.commit()


async def get_order_by_message(
    db_path: str, chat_id: int, message_id: int
) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT o.* FROM orders o
            JOIN order_messages m ON o.id = m.order_id
            WHERE m.chat_id=? AND m.message_id=?
            """,
            (chat_id, message_id),
        )
        return await cursor.fetchone()


async def get_message_record(
    db_path: str, chat_id: int, message_id: int
) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM order_messages WHERE chat_id=? AND message_id=?",
            (chat_id, message_id),
        )
        return await cursor.fetchone()


async def get_message_record_for_role(
    db_path: str, order_id: int, role: str
) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM order_messages WHERE order_id=? AND role=?",
            (order_id, role),
        )
        return await cursor.fetchone()


async def get_order_messages(db_path: str, order_id: int) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM order_messages WHERE order_id=?",
            (order_id,),
        )
        return await cursor.fetchall()


async def get_order(db_path: str, order_id: int) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        return await cursor.fetchone()


async def update_order_status(
    db_path: str,
    order_id: int,
    from_status: str,
    to_status: str,
    actor_field: Optional[str] = None,
    actor_id: Optional[int] = None,
    timestamp_field: Optional[str] = None,
) -> bool:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        assignments = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        values: list[object] = [to_status]
        if actor_field and actor_id is not None:
            assignments.append(f"{actor_field} = ?")
            values.append(actor_id)
        if timestamp_field:
            assignments.append(f"{timestamp_field} = CURRENT_TIMESTAMP")
        values.extend([order_id, from_status])
        cursor = await db.execute(
            f"""
            UPDATE orders
            SET {", ".join(assignments)}
            WHERE id = ? AND status = ?
            """,
            tuple(values),
        )
        await db.commit()
        return cursor.rowcount == 1


async def set_route(db_path: str, order_type: str, cp_pack: Optional[int], chat_id: int) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO routes(type, cp_pack, chat_id)
            VALUES(?, ?, ?)
            ON CONFLICT(type, cp_pack) DO UPDATE SET
                chat_id=excluded.chat_id
            """,
            (order_type, cp_pack, chat_id),
        )
        await db.commit()


async def get_route(db_path: str, order_type: str, cp_pack: int) -> Optional[int]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT chat_id FROM routes WHERE type=? AND cp_pack=?",
            (order_type, cp_pack),
        )
        row = await cursor.fetchone()
        return row["chat_id"] if row else None


async def get_main_route(db_path: str) -> Optional[int]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT chat_id FROM routes WHERE type='main' AND cp_pack IS NULL"
        )
        row = await cursor.fetchone()
        return row["chat_id"] if row else None


async def list_routes(db_path: str) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT type, cp_pack, chat_id FROM routes ORDER BY type, cp_pack"
        )
        return await cursor.fetchall()


async def create_cancel_request(
    db_path: str,
    order_id: int,
    worker_chat_id: int,
    worker_message_id: int,
    request_message_id: int,
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO cancel_requests(
                order_id,
                worker_chat_id,
                worker_message_id,
                request_message_id,
                status
            ) VALUES(?, ?, ?, ?, 'pending')
            """,
            (order_id, worker_chat_id, worker_message_id, request_message_id),
        )
        await db.commit()


async def get_cancel_request(db_path: str, order_id: int) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM cancel_requests WHERE order_id=?",
            (order_id,),
        )
        return await cursor.fetchone()


async def update_cancel_request_status(
    db_path: str, order_id: int, status: str, decided_by: Optional[int]
) -> bool:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            """
            UPDATE cancel_requests
            SET status=?, decided_by=?, decided_at=CURRENT_TIMESTAMP
            WHERE order_id=? AND status='pending'
            """,
            (status, decided_by, order_id),
        )
        await db.commit()
        return cursor.rowcount == 1
