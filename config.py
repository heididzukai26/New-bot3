"""Configuration file for the Telegram bot."""

import os

# Bot token from environment variable
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# Database file path
DB_PATH = 'bot_database.db'

# Worker group IDs for routing
# Format: {'keyword': -100123456789, ...}
ROUTING_TABLE = {
    # Add worker group IDs here
    # Example: 'urgent': -1001234567890,
}

# Main fallback group ID (used when no routing match)
MAIN_FALLBACK_GROUP = os.getenv('MAIN_GROUP_ID', 'YOUR_MAIN_GROUP_ID_HERE')
