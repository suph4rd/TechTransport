import re


def normalize_phone(value: str):
    if not re.fullmatch(r"[+0-9 ()-]+", value):
        raise ValueError("Введите белорусский номер телефона")
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("80"):
        digits = "375" + digits[2:]
    elif len(digits) == 9:
        digits = "375" + digits
    if not re.fullmatch(r"375(?:25|29|33|44)\d{7}", digits):
        raise ValueError("Введите мобильный номер Беларуси: +375 XX XXX XX XX")
    return "+" + digits


def clean_name(value: str):
    value = value.strip()
    if not value or any(ord(c) < 32 for c in value):
        raise ValueError("Укажите имя без управляющих символов")
    return value
