"""Database operations for the bot."""

import sqlite3
from datetime import datetime
import config


def init_db():
    """
    Initialize the database and create necessary tables.
    Creates orders table if it doesn't exist.
    """
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            message_text TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            line_count INTEGER,
            routed_to TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")


def save_order(user_id, username, message_text, email, phone, line_count, routed_to):
    """
    Save an order to the database.
    
    Args:
        user_id (int): Telegram user ID
        username (str): Telegram username
        message_text (str): Full message text
        email (str): Extracted email address
        phone (str): Extracted phone number
        line_count (int): Number of lines in message
        routed_to (str): Group ID where order was routed
        
    Returns:
        int: ID of the saved order
    """
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO orders 
        (user_id, username, message_text, email, phone, line_count, routed_to)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, message_text, email, phone, line_count, routed_to))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return order_id


def get_order(order_id):
    """
    Retrieve an order by ID.
    
    Args:
        order_id (int): Order ID
        
    Returns:
        dict or None: Order data if found, None otherwise
    """
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_order_status(order_id, status):
    """
    Update the status of an order.
    
    Args:
        order_id (int): Order ID
        status (str): New status value
        
    Returns:
        bool: True if update successful, False otherwise
    """
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE orders 
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, order_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success
