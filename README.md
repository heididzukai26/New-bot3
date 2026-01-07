# Telegram Order Management Bot

Python Telegram bot for routing and tracking customer orders with SQLite persistence.

## Setup
1. Install Python 3.11+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set:
   - `BOT_TOKEN` – Telegram bot token
   - `DATABASE_PATH` – SQLite file path (default `bot.db`)
   - `ADMIN_IDS` – comma-separated admin user IDs for pricing/export
4. Run the bot:
   ```bash
   python main.py
   ```

## Commands
- `/addsource <type> <amount>` – register current group as worker for exact type+amount.
- `/addsource main` – register current group as main fallback.
- `/listsources` – show all mappings.
- `/invoice` – show recorded totals (admins only).
- `/export` – download XLSX export (admins only).

## Flows
- **Order detection**: customer message must have ≥3 lines, an email, and a number. Type parsed from text (`fund`, `unsafe`, `safe_fast`, `safe_slow`), amount is largest number.
- **Routing**: exact type+amount goes to worker mapping; otherwise to main group. Customer IDs are never shown to workers.
- **Worker actions**: reply `done` to deliver; reply `wrong` to reject. Reactions added where supported.
- **Cancel**: customer replies to their order with `cancel/کنسل/لغو`; worker receives Approve/Reject inline prompt.
- **Pricing**: admins reply with `50$` or `7200tm` to an order message to record price and update invoice totals.

## Test checklist (manual)
- Send a 3+ line message with email and number → order saved and routed.
- `/addsource` and `/listsources` reflect new mappings and main fallback.
- Worker replies `done`/`wrong` update status, reactions appear, and customer notified.
- Customer cancel request triggers inline decision in worker group; approval rejects delivery and adds 👎.
- Admin price reply records totals; `/invoice` returns sums; `/export` downloads XLSX without secrets.
