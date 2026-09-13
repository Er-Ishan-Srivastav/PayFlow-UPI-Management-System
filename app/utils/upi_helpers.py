import re

UPI_PATTERN = re.compile(r"^[a-zA-Z0-9.\-_]{3,}@[a-zA-Z]{2,}$")


def is_valid_upi(upi_id: str) -> bool:
    return bool(upi_id and UPI_PATTERN.match(upi_id.strip()))


def make_upi_address(handle: str, provider: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9.\-_]", "", (handle or "").lower())
    provider = (provider or "payflow").lstrip("@").lower()
    return f"{clean}@{provider}"
