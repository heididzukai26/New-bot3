"""Utility functions for the bot."""

import re


def extract_email(text):
    """
    Extract email address from text.
    
    Args:
        text (str): Text to search for email
        
    Returns:
        str or None: Email address if found, None otherwise
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None


def extract_phone_number(text):
    """
    Extract phone number from text.
    Supports various formats: +1234567890, (123) 456-7890, 123-456-7890, etc.
    
    Args:
        text (str): Text to search for phone number
        
    Returns:
        str or None: Phone number if found, None otherwise
    """
    # Pattern for phone numbers with various formats
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def count_lines(text):
    """
    Count non-empty lines in text.
    
    Args:
        text (str): Text to count lines in
        
    Returns:
        int: Number of non-empty lines
    """
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    return len(lines)
