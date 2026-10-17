"""Money helpers for susu contributions, stored as integer pesewas."""

from decimal import Decimal, InvalidOperation
import re


def parse_money(value):
    """Convert a GHS amount string into integer pesewas.

    Accepts whole cedis or one/two decimal places, e.g. 50, 50.0, 12.50.
    """
    value = value.strip()
    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", value):
        raise ValueError("Enter a valid amount, e.g. 50, 50.00, or 12.50.")

    try:
        amount = Decimal(value)
    except InvalidOperation:
        raise ValueError("Invalid money amount.") from None

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    return int(amount * 100)


def format_money(pesewas):
    """Convert integer pesewas into a GHS display string, e.g. GHS 50.00."""
    cedis = pesewas // 100
    remaining = pesewas % 100
    return f"GHS {cedis}.{remaining:02d}"
