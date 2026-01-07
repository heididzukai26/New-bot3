# New-bot3 - Telegram Order Bot

A modular Python Telegram bot that uses long polling to detect and route orders to worker groups.

## Features

- 🤖 Long polling Telegram bot
- 📋 Automatic order detection (3+ lines, email, phone number)
- 💾 SQLite database for order storage
- 🔀 Smart routing to worker groups via routing table with main fallback
- 📦 Modular code structure

## Project Structure

```
.
├── main.py          # Bot initialization and message handling
├── db.py            # Database operations
├── routing.py       # Order routing logic
├── orders.py        # Order detection and validation
├── utils.py         # Helper functions
├── config.py        # Configuration settings
└── requirements.txt # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/heididzukai26/New-bot3.git
cd New-bot3
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
   - Set `TELEGRAM_BOT_TOKEN` environment variable with your bot token
   - Set `MAIN_GROUP_ID` environment variable with your main group ID
   - Or edit `config.py` directly

## Configuration

Edit `config.py` to configure:
- Bot token
- Database path
- Routing table (keyword to group ID mapping)
- Main fallback group ID

Example routing table:
```python
ROUTING_TABLE = {
    'urgent': -1001234567890,
    'priority': -1009876543210,
}
```

## Usage

Run the bot:
```bash
python main.py
```

The bot will:
1. Initialize the database on first run
2. Start long polling for messages
3. Detect valid orders (3+ lines + email + phone)
4. Save orders to database
5. Route orders to appropriate worker groups

### Order Format

Send a message with:
- At least 3 lines of text
- A valid email address
- A phone number

Example:
```
I need 5 blue widgets
Please ship to warehouse A
Contact: john@example.com
Phone: +1-555-0123
```

## Placeholders for Future Features

The following functions are defined but not yet implemented:
- `cancel_order()` - Cancel an order
- `mark_order_done()` - Mark order as complete
- `mark_order_wrong()` - Mark order as incorrect
- `calculate_pricing()` - Calculate order pricing
- `export_orders()` - Export orders to CSV/other formats
- `update_routing_table()` - Dynamically update routing

## Database Schema

Orders table:
- `id` - Auto-incrementing primary key
- `user_id` - Telegram user ID
- `username` - Telegram username
- `message_text` - Full order text
- `email` - Extracted email
- `phone` - Extracted phone number
- `line_count` - Number of lines in order
- `routed_to` - Group ID where routed
- `status` - Order status (default: 'pending')
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

## License

MIT
