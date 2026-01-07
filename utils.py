import re
from typing import Dict, Iterable, Optional, Tuple

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?")


def extract_email(text: str) -> Optional[str]:
    """
    Return the first email address found anywhere in the text.
    """
    match = EMAIL_PATTERN.search(text or "")
    return match.group(0) if match else None


def contains_email(text: str) -> bool:
    """
    True if any email address appears in the text.
    """
    return extract_email(text) is not None


def cp_amount(text: str) -> Optional[float]:
    """
    Largest numeric value found in the text. Returns None if no numbers exist.
    """
    numbers = NUMBER_PATTERN.findall(text or "")
    if not numbers:
        return None
    parsed_numbers = [float(num) for num in numbers]
    return max(parsed_numbers)


def _line_items(text: str) -> Tuple[str, ...]:
    return tuple(line.strip() for line in (text or "").splitlines() if line.strip())


def is_order(text: str) -> bool:
    """
    Order rule: at least 3 non-empty lines, contains an email and a number.
    """
    lines = _line_items(text)
    return len(lines) >= 3 and contains_email(text) and cp_amount(text) is not None


def order_type(text: str) -> Optional[str]:
    lines = _line_items(text)
    return lines[0] if lines else None


def parse_order(text: str) -> Optional[Dict[str, object]]:
    if not is_order(text):
        return None
    return {
        "type": order_type(text),
        "email": extract_email(text),
        "cp_amount": cp_amount(text),
        "raw": text,
    }


def route_orders(messages: Iterable[str]) -> Dict[Tuple[str, float], Dict[str, object]]:
    """
    Save orders keyed by (type, cp_amount). Last write wins for identical keys.
    """
    routed: Dict[Tuple[str, float], Dict[str, object]] = {}
    for message in messages:
        order = parse_order(message)
        if order is None:
            continue
        key = (order["type"], order["cp_amount"])
        routed[key] = order
    return routed
