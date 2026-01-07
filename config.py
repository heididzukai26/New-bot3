"""Configuration file for the Telegram bot."""

import os
import sys

# Bot token from environment variable
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    print("Warning: TELEGRAM_BOT_TOKEN environment variable not set.")
    print("Please set it with: export TELEGRAM_BOT_TOKEN='your_token_here'")
    print("Or edit config.py to set BOT_TOKEN directly.")
    BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Fallback for testing

# Database file path
DB_PATH = 'bot_database.db'

# Worker group IDs for routing
# Format: {'keyword': -100123456789, ...}
ROUTING_TABLE = {
    # Add worker group IDs here
    # Example: 'urgent': -1001234567890,
}

# Main fallback group ID (used when no routing match)
MAIN_FALLBACK_GROUP = os.getenv('MAIN_GROUP_ID')
if not MAIN_FALLBACK_GROUP:
    print("Warning: MAIN_GROUP_ID environment variable not set.")
    print("Please set it with: export MAIN_GROUP_ID='-1001234567890'")
    print("Or edit config.py to set MAIN_FALLBACK_GROUP directly.")
    MAIN_FALLBACK_GROUP = 'YOUR_MAIN_GROUP_ID_HERE'  # Fallback for testing
