"""Rotating savings group (susu) with exact GHS money handling."""

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


class SusuGroup:
    """One susu group with a fixed weekly contribution and ordered members."""

    def __init__(self, weekly_contribution):
        if weekly_contribution <= 0:
            raise ValueError("Weekly contribution must be positive.")

        self.weekly_contribution = weekly_contribution
        self.members = {}
        self.member_order = []
        self.payments = {}
        self.payout_history = []
        self.current_week = 1
        self.started = False

    def add_member(self, name):
        name = name.strip()
        if not name:
            raise ValueError("Member name cannot be empty.")

        key = name.casefold()
        if key in self.members:
            raise ValueError(f"Member '{name}' already exists.")

        if self.started:
            raise ValueError("Members cannot be added after contributions begin.")

        self.members[key] = name
        self.member_order.append(key)
        self.payments[key] = 0
        return name
