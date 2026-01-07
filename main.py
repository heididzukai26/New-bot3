"""
Main module for the Telegram bot.
Implements long polling and order processing.
"""

import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

import config
import db
from orders import is_valid_order, parse_order
from routing import determine_route

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text(
        "Welcome to the Order Bot! 🤖\n\n"
        "Send me an order message with:\n"
        "- At least 3 lines\n"
        "- An email address\n"
        "- A phone number\n\n"
        "I'll process and route your order automatically."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command."""
    help_text = """
📋 Order Bot Help

To submit an order, send a message with:
✓ At least 3 lines of text
✓ A valid email address
✓ A phone number

Example:
```
I need 5 blue widgets
Please ship to warehouse A
Contact: john@example.com
Phone: +1-555-0123
```

The bot will automatically detect valid orders and route them to the appropriate worker group.
"""
    await update.message.reply_text(help_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming messages and process potential orders.
    """
    message = update.message
    text = message.text
    
    if not text:
        return
    
    # Check if message is a valid order
    if is_valid_order(text):
        logger.info(f"Valid order detected from user {message.from_user.id}")
        
        # Parse order information
        order_info = parse_order(text)
        
        # Determine routing
        target_group = determine_route(text)
        
        # Save order to database
        order_id = db.save_order(
            user_id=message.from_user.id,
            username=message.from_user.username or "Unknown",
            message_text=text,
            email=order_info['email'],
            phone=order_info['phone'],
            line_count=order_info['line_count'],
            routed_to=target_group
        )
        
        logger.info(f"Order {order_id} saved and routed to {target_group}")
        
        # Confirm to user
        await message.reply_text(
            f"✅ Order received and processed!\n\n"
            f"Order ID: {order_id}\n"
            f"Email: {order_info['email']}\n"
            f"Phone: {order_info['phone']}\n"
            f"Routed to: {target_group}\n\n"
            f"Your order will be handled by our team shortly."
        )
        
        # Forward to target group
        try:
            # Note: This requires the bot to be added to the target group
            await context.bot.send_message(
                chat_id=target_group,
                text=f"📦 New Order #{order_id}\n"
                     f"From: @{message.from_user.username or 'User'} (ID: {message.from_user.id})\n"
                     f"Email: {order_info['email']}\n"
                     f"Phone: {order_info['phone']}\n\n"
                     f"Order Details:\n{text}"
            )
            logger.info(f"Order {order_id} forwarded to group {target_group}")
        except Exception as e:
            logger.error(f"Failed to forward order {order_id} to group {target_group}: {e}")
            # Order is still saved in database even if forwarding fails
    else:
        logger.debug(f"Message from {message.from_user.id} is not a valid order")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Main function to start the bot."""
    # Initialize database
    logger.info("Initializing database...")
    db.init_db()
    
    # Create application
    logger.info("Starting bot...")
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot with long polling
    logger.info("Bot is running... Press Ctrl+C to stop")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
