# CODM Order Management Bot (Telegram)

Async Telegram bot for routing and tracking CODM CP orders with SQLite persistence.

## Requirements
- Python 3.11+

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and set:
   - `BOT_TOKEN` – Telegram bot token
   - `ADMIN_IDS` – comma-separated admin user IDs
   - `DB_PATH` – SQLite file path (default `bot.db`)
3. Run the bot:
   ```bash
   python main.py
   ```

## Commands
- `/addsource <type> <pack>` – register current group as source for exact type+pack.
- `/addsource main` – register current group as main fallback.
- `/listsources` – list configured source routes.

## Behavior Highlights
- Customer messages are bilingual (FA/EN).
- Orders are accepted only if the message has 3+ lines, contains an email, and includes a valid CP pack or a total that maps to one.
- Order type detection supports: `safe_fast`, `safe_slow`, `unsafe`, `fund`.
- Routing is based on `(type, cp_pack)` with fallback to `main`.
- Canonical order messages are posted to the customer group (reply) and the source group (new message).
- Worker actions (`done`, `wrong`, or photo with `done` caption) only work when replying to canonical source messages.
- Customers can request cancellation by replying `cancel/کنسل/لغو` to their canonical order message; source staff approve or reject via inline buttons.
