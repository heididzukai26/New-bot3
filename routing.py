"""Routing logic for orders to worker groups."""

import config


def determine_route(message_text):
    """
    Determine which group to route an order to based on routing table.
    Falls back to main group if no match found.
    
    Args:
        message_text (str): Order message text
        
    Returns:
        str: Group ID to route the order to
    """
    message_lower = message_text.lower()
    
    # Check routing table for keyword matches
    for keyword, group_id in config.ROUTING_TABLE.items():
        if keyword.lower() in message_lower:
            return str(group_id)
    
    # Fallback to main group
    return str(config.MAIN_FALLBACK_GROUP)


def get_routing_info():
    """
    Get current routing configuration.
    
    Returns:
        dict: Routing table and main fallback group
    """
    return {
        'routing_table': config.ROUTING_TABLE,
        'main_fallback': config.MAIN_FALLBACK_GROUP
    }


# Placeholder function for future routing enhancements
def update_routing_table(keyword, group_id):
    """Placeholder: Update routing table dynamically."""
    raise NotImplementedError("Dynamic routing table update to be implemented")
