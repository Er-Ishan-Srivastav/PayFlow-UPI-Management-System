import re

UPI_PATTERN = re.compile(r'^[a-zA-Z0-9.\-_]{3,}@[a-zA-Z]{3,}$')

def is_valid_upi(upi_id: str) -> bool:
    """Validate UPI ID format (simplified)."""
    return bool(UPI_PATTERN.match(upi_id))

def generate_upi_id(handle: str, provider: str = 'payflow') -> str:
    """Generate a UPI ID from handle."""
    clean = re.sub(r'[^a-zA-Z0-9.\-_]', '', handle.lower())
    return f"{clean}@{provider}"
