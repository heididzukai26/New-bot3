import re
from typing import Optional


EMAIL_REGEX = re.compile(
    r"^(?!.*\.\.)[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)
NUMBER_REGEX = re.compile(r"\d[\d,]*")
PRICE_REGEX = re.compile(r"(\d[\d,]*)(\$|tm)", re.IGNORECASE)


def contains_email(text: str) -> bool:
    return bool(EMAIL_REGEX.search(text))


def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def extract_numbers(text: str) -> list[int]:
    numbers: list[int] = []
    for raw in NUMBER_REGEX.findall(text):
        cleaned = raw.replace(",", "")
        if cleaned.isdigit():
            numbers.append(int(cleaned))
    return numbers


def largest_number(text: str) -> Optional[int]:
    numbers = extract_numbers(text)
    return max(numbers) if numbers else None


def parse_order_type(text: str) -> str:
    lowered = text.lower()
    if "unsafe" in lowered:
        return "unsafe"
    if "safe_fast" in lowered or "safe fast" in lowered or ("safe" in lowered and "fast" in lowered):
        return "safe_fast"
    if "safe_slow" in lowered or "safe slow" in lowered or ("safe" in lowered and "slow" in lowered):
        return "safe_slow"
    if "safe" in lowered:
        return "safe_slow"
    return "fund"


def is_order_message(text: str) -> bool:
    if not text:
        return False
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return len(lines) >= 3 and contains_email(text) and bool(NUMBER_REGEX.search(text))


def parse_price(text: str) -> Optional[tuple[float, str]]:
    match = PRICE_REGEX.search(text)
    if not match:
        return None
    cleaned = match.group(1).replace(",", "")
    if not cleaned.isdigit():
        return None
    amount = float(cleaned)
    currency = "USD" if match.group(2) == "$" else "TM"
    return amount, currency
