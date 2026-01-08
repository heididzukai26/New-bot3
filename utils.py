import re
from dataclasses import dataclass
from typing import Optional


VALID_PACKS = [80, 420, 880, 2400, 5000, 10800]

EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PACK_PATTERN = r"(?:80|420|880|2400|5000|10800)"


@dataclass
class ParsedOrder:
    order_type: str
    cp_pack: int
    cp_qty: int
    cp_total: int
    email: str
    password: str
    ign: Optional[str]


def normalize_type(text: str) -> Optional[str]:
    lowered = text.lower()
    if re.search(r"\bsafe[\s_-]*fast\b", lowered):
        return "safe_fast"
    if re.search(r"\bsafe[\s_-]*slow\b", lowered):
        return "safe_slow"
    if re.search(r"\bunsafe\b", lowered):
        return "unsafe"
    if re.search(r"\bfund\b", lowered):
        return "fund"
    return None


def extract_email(text: str) -> Optional[str]:
    match = EMAIL_REGEX.search(text)
    return match.group(0) if match else None


def _clean_number(value: str) -> Optional[int]:
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def extract_numbers(text: str) -> list[int]:
    numbers = []
    for match in re.findall(r"\d+[\d,]*", text):
        value = _clean_number(match)
        if value is not None:
            numbers.append(value)
    return numbers


def parse_cp_pack(text: str) -> Optional[tuple[int, int, int]]:
    multiplier_patterns = [
        rf"(?P<pack>{PACK_PATTERN})\s*[x×*]\s*(?P<qty>\d+)",
        rf"(?P<qty>\d+)\s*[x×*]\s*(?P<pack>{PACK_PATTERN})",
    ]
    for pattern in multiplier_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            pack = int(match.group("pack"))
            qty = int(match.group("qty"))
            if qty > 0:
                return pack, qty, pack * qty

    numbers = extract_numbers(text)
    packs_in_text = [n for n in numbers if n in VALID_PACKS]
    if packs_in_text:
        pack = max(packs_in_text)
        return pack, 1, pack

    for number in sorted(numbers, reverse=True):
        for pack in sorted(VALID_PACKS, reverse=True):
            if number % pack == 0:
                qty = number // pack
                if qty > 0:
                    return pack, qty, number

    return None


def parse_password(lines: list[str], email_line_index: Optional[int]) -> Optional[str]:
    for line in lines:
        if re.search(r"\b(pass|password)\b", line, re.IGNORECASE) or "پسورد" in line or "رمز" in line:
            parts = re.split(r"[:：]", line, maxsplit=1)
            if len(parts) == 2:
                value = parts[1].strip()
                if value:
                    return value
            stripped = re.sub(r"\b(pass|password)\b", "", line, flags=re.IGNORECASE)
            stripped = stripped.replace("پسورد", "").replace("رمز", "").strip("-:： ")
            if stripped:
                return stripped
    if email_line_index is not None:
        for line in lines[email_line_index + 1 :]:
            if line:
                return line
    return None


def parse_ign(lines: list[str]) -> Optional[str]:
    for line in lines:
        if re.search(r"\bign\b", line, re.IGNORECASE) or "in game" in line.lower() or "نام" in line:
            parts = re.split(r"[:：]", line, maxsplit=1)
            value = parts[1].strip() if len(parts) == 2 else line
            value = re.sub(r"\bign\b", "", value, flags=re.IGNORECASE).strip("-:： ")
            if value:
                return value
    return None


def parse_order(text: str) -> Optional[ParsedOrder]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        return None
    email = extract_email(text)
    if not email:
        return None

    email_line_index = None
    for idx, line in enumerate(lines):
        if email in line:
            email_line_index = idx
            break

    order_type = normalize_type(text)
    if not order_type:
        return ParsedOrder(order_type="", cp_pack=0, cp_qty=0, cp_total=0, email=email, password="", ign=None)

    cp_data = parse_cp_pack(text)
    if not cp_data:
        return ParsedOrder(order_type=order_type, cp_pack=0, cp_qty=0, cp_total=0, email=email, password="", ign=None)
    cp_pack, cp_qty, cp_total = cp_data

    password = parse_password(lines, email_line_index)
    if not password:
        return ParsedOrder(
            order_type=order_type,
            cp_pack=cp_pack,
            cp_qty=cp_qty,
            cp_total=cp_total,
            email=email,
            password="",
            ign=None,
        )

    ign = parse_ign(lines)
    return ParsedOrder(
        order_type=order_type,
        cp_pack=cp_pack,
        cp_qty=cp_qty,
        cp_total=cp_total,
        email=email,
        password=password,
        ign=ign,
    )


def canonical_status(status: str) -> tuple[str, str]:
    mapping = {
        "pending": ("⏳ Pending", "⏳ در انتظار"),
        "pending_cancel": ("⏳ Pending (Cancel Requested)", "⏳ در انتظار (درخواست لغو)"),
        "completed": ("✅ Completed", "✅ تکمیل شد"),
        "cancelled": ("👎 Cancelled", "👎 لغو شد"),
        "rejected": ("👎 Rejected", "👎 رد شد"),
    }
    return mapping.get(status, (status, status))


def build_canonical_message(order: dict) -> str:
    ign_line = f"IGN: {order['ign']} / نام بازی: {order['ign']}\n" if order.get("ign") else ""
    status_en, status_fa = canonical_status(order["status"])
    return (
        f"Order #{order['id']}\n"
        f"Type: {order['type']} / نوع: {order['type']}\n"
        f"CP: {order['cp_pack']} x{order['cp_qty']} (Total: {order['cp_total']}) / سی‌پی: {order['cp_pack']} ×{order['cp_qty']} (جمع: {order['cp_total']})\n"
        f"Email: {order['email']} / ایمیل: {order['email']}\n"
        f"Password: {order['password']} / رمز: {order['password']}\n"
        f"{ign_line}"
        f"Status: {status_en} / وضعیت: {status_fa}"
    )


def is_cancel_text(text: str) -> bool:
    lowered = text.lower().strip()
    return lowered in {"cancel", "کنسل", "لغو"}


def is_done_text(text: str) -> bool:
    return text.lower().strip() == "done"


def is_wrong_text(text: str) -> bool:
    return text.lower().strip() in {"wrong", "❌"}


def parse_price_amount(text: str) -> Optional[tuple[float, str]]:
    if is_done_text(text) or is_wrong_text(text) or is_cancel_text(text):
        return None
    usd_match = re.fullmatch(r"\$\s?(\d+(?:[\.,]\d+)?)", text.strip())
    if usd_match:
        return float(usd_match.group(1).replace(",", ".")), "USD"
    usd_match = re.fullmatch(r"(\d+(?:[\.,]\d+)?)\$", text.strip())
    if usd_match:
        return float(usd_match.group(1).replace(",", ".")), "USD"
    toman_match = re.fullmatch(r"(\d+(?:[\.,]\d+)?)\s*tm", text.strip(), re.IGNORECASE)
    if toman_match:
        return float(toman_match.group(1).replace(",", ".")), "TOMAN"
    toman_match = re.fullmatch(r"(\d+(?:[\.,]\d+)?)\s*تومان", text.strip())
    if toman_match:
        return float(toman_match.group(1).replace(",", ".")), "TOMAN"
    return None
