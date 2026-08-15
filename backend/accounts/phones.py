import re

EGYPTIAN_MOBILE = re.compile(r"^01[0-9]{9}$")
INVALID_PHONE_MESSAGE = "Enter an Egyptian mobile number like 01xxxxxxxxx."


class InvalidPhone(ValueError):
    pass


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"[\s\-]", "", (raw or "").strip())
    if digits.startswith("+20"):
        digits = "0" + digits[3:]
    elif digits.startswith("20") and len(digits) == 12:
        digits = "0" + digits[2:]
    if not EGYPTIAN_MOBILE.fullmatch(digits):
        raise InvalidPhone(INVALID_PHONE_MESSAGE)
    return digits
