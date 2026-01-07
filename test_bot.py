"""Test script to validate order detection and core functionality."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from orders import is_valid_order, parse_order
from utils import extract_email, extract_phone_number, count_lines
import db
import routing


def test_utils():
    """Test utility functions."""
    print("Testing utility functions...")
    
    # Test email extraction
    email = extract_email("Contact me at john@example.com for details")
    assert email == "john@example.com", f"Email extraction failed: {email}"
    print("✓ Email extraction works")
    
    # Test phone extraction
    phone = extract_phone_number("Call me at +1-555-0123")
    assert phone is not None, "Phone extraction failed"
    print(f"✓ Phone extraction works: {phone}")
    
    # Test line counting
    text = "Line 1\nLine 2\nLine 3\n\nLine 5"
    lines = count_lines(text)
    assert lines == 4, f"Line count incorrect: {lines}"
    print(f"✓ Line counting works: {lines} lines")


def test_order_validation():
    """Test order validation logic."""
    print("\nTesting order validation...")
    
    # Valid order
    valid_order = """I need 5 blue widgets
Please ship to warehouse A
Contact: john@example.com
Phone: +1-555-0123"""
    
    assert is_valid_order(valid_order), "Valid order not detected"
    print("✓ Valid order detected correctly")
    
    # Invalid - only 2 lines
    invalid_short = """Contact: john@example.com
Phone: +1-555-0123"""
    assert not is_valid_order(invalid_short), "Short message incorrectly validated"
    print("✓ Short message rejected correctly")
    
    # Invalid - no email
    invalid_no_email = """Line 1
Line 2
Phone: +1-555-0123"""
    assert not is_valid_order(invalid_no_email), "Message without email incorrectly validated"
    print("✓ Message without email rejected correctly")
    
    # Invalid - no phone
    invalid_no_phone = """Line 1
Line 2
Email: john@example.com"""
    assert not is_valid_order(invalid_no_phone), "Message without phone incorrectly validated"
    print("✓ Message without phone rejected correctly")


def test_order_parsing():
    """Test order parsing."""
    print("\nTesting order parsing...")
    
    order_text = """I need urgent delivery
Address: 123 Main St
Contact: alice@company.com
Phone: (555) 123-4567"""
    
    parsed = parse_order(order_text)
    assert parsed['email'] == 'alice@company.com', f"Email parsing failed: {parsed['email']}"
    assert parsed['phone'] is not None, f"Phone parsing failed: {parsed['phone']}"
    assert parsed['line_count'] == 4, f"Line count incorrect: {parsed['line_count']}"
    print(f"✓ Order parsed correctly: {parsed}")


def test_database():
    """Test database operations."""
    print("\nTesting database operations...")
    
    # Initialize database
    db.init_db()
    print("✓ Database initialized")
    
    # Save an order
    order_id = db.save_order(
        user_id=12345,
        username="testuser",
        message_text="Test order\nLine 2\nemail@test.com\n555-1234",
        email="email@test.com",
        phone="555-1234",
        line_count=4,
        routed_to="-100123456"
    )
    assert order_id > 0, "Order save failed"
    print(f"✓ Order saved with ID: {order_id}")
    
    # Retrieve order
    order = db.get_order(order_id)
    assert order is not None, "Order retrieval failed"
    assert order['email'] == "email@test.com", "Order data incorrect"
    print(f"✓ Order retrieved correctly")
    
    # Update order status
    success = db.update_order_status(order_id, "completed")
    assert success, "Order status update failed"
    print("✓ Order status updated")


def test_routing():
    """Test routing logic."""
    print("\nTesting routing logic...")
    
    # Test fallback routing (no keywords)
    route = routing.determine_route("Normal order without keywords")
    print(f"✓ Fallback routing works: {route}")
    
    # Test with routing table (if configured)
    info = routing.get_routing_info()
    print(f"✓ Routing info retrieved: {info['main_fallback']}")


def main():
    """Run all tests."""
    print("=" * 50)
    print("Running Bot Core Functionality Tests")
    print("=" * 50)
    
    try:
        test_utils()
        test_order_validation()
        test_order_parsing()
        test_database()
        test_routing()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
