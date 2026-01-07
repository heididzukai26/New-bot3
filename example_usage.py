"""
Example usage and setup guide for the Order Bot.

This file demonstrates how to configure and run the bot.
"""

# Step 1: Get your bot token from @BotFather on Telegram
# Set it as an environment variable:
# export TELEGRAM_BOT_TOKEN="your_bot_token_here"

# Step 2: Create a group for receiving orders
# Add your bot to the group
# Get the group ID (you can use @userinfobot or check logs)
# export MAIN_GROUP_ID="-1001234567890"

# Step 3: (Optional) Configure routing table in config.py
# Example:
"""
ROUTING_TABLE = {
    'urgent': -1001111111111,    # Orders with "urgent" keyword go here
    'priority': -1002222222222,   # Orders with "priority" keyword go here
    'express': -1003333333333,    # Orders with "express" keyword go here
}
"""

# Step 4: Run the bot
# python main.py

# Example valid order message:
EXAMPLE_ORDER = """
Product: 10 Premium Widgets
Delivery Address: 123 Main Street, City, State 12345
Special Instructions: Please handle with care

Contact Information:
Email: customer@example.com
Phone: +1 (555) 123-4567
Preferred delivery time: 9 AM - 5 PM
"""

# The bot will:
# 1. Detect this as a valid order (3+ lines, email, phone)
# 2. Extract: email=customer@example.com, phone=+1 (555) 123-4567
# 3. Check routing table for keywords
# 4. Save to database
# 5. Forward to appropriate worker group
# 6. Confirm to user with order ID

print("Example Order Bot Configuration")
print("=" * 60)
print("\n1. Set environment variables:")
print("   export TELEGRAM_BOT_TOKEN='your_token_here'")
print("   export MAIN_GROUP_ID='-1001234567890'")
print("\n2. Configure routing in config.py (optional)")
print("\n3. Run: python main.py")
print("\n4. Send order messages like:")
print(EXAMPLE_ORDER)
print("=" * 60)
