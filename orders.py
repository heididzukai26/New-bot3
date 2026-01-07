"""Order detection and validation logic."""

from utils import extract_email, extract_phone_number, count_lines


def is_valid_order(text):
    """
    Check if a message is a valid order.
    Valid order criteria:
    - At least 3 lines of text
    - Contains an email address
    - Contains a phone number
    
    Args:
        text (str): Message text to validate
        
    Returns:
        bool: True if message is a valid order, False otherwise
    """
    if not text:
        return False
    
    # Check line count
    line_count = count_lines(text)
    if line_count < 3:
        return False
    
    # Check for email
    email = extract_email(text)
    if not email:
        return False
    
    # Check for phone number
    phone = extract_phone_number(text)
    if not phone:
        return False
    
    return True


def parse_order(text):
    """
    Parse order information from message text.
    
    Args:
        text (str): Message text to parse
        
    Returns:
        dict: Order information with keys: text, email, phone, line_count
    """
    return {
        'text': text,
        'email': extract_email(text),
        'phone': extract_phone_number(text),
        'line_count': count_lines(text)
    }


# Placeholder functions for future implementation
def cancel_order(order_id):
    """Placeholder: Cancel an order."""
    raise NotImplementedError("Cancel order functionality to be implemented")


def mark_order_done(order_id):
    """Placeholder: Mark an order as done."""
    raise NotImplementedError("Mark order done functionality to be implemented")


def mark_order_wrong(order_id):
    """Placeholder: Mark an order as wrong."""
    raise NotImplementedError("Mark order wrong functionality to be implemented")


def calculate_pricing(order_id):
    """Placeholder: Calculate pricing for an order."""
    raise NotImplementedError("Pricing calculation to be implemented")


def export_orders(format='csv'):
    """Placeholder: Export orders to specified format."""
    raise NotImplementedError("Export orders functionality to be implemented")
