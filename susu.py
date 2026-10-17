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

    def remaining_this_week(self, key):
        return self.weekly_contribution - self.payments[key]

    def record_contribution(self, name, amount):
        key = name.strip().casefold()
        if key not in self.members:
            raise ValueError(f"Unknown member: '{name}'.")

        if amount <= 0:
            raise ValueError("Contribution must be greater than zero.")

        remaining = self.remaining_this_week(key)
        if amount > remaining:
            raise ValueError(
                f"{self.members[key]} owes only {format_money(remaining)} this week."
            )

        self.payments[key] += amount
        self.started = True
        return {
            "name": self.members[key],
            "week": self.current_week,
            "paid": amount,
            "total_paid": self.payments[key],
            "owes": self.remaining_this_week(key),
        }

    def outstanding_balances(self):
        outstanding = []
        for key in self.member_order:
            owed = self.remaining_this_week(key)
            if owed > 0:
                outstanding.append({"name": self.members[key], "owes": owed})
        return outstanding

    def close_week(self):
        if not self.member_order:
            raise ValueError("Add at least one member before closing a week.")

        outstanding = self.outstanding_balances()
        if outstanding:
            return {
                "closed": False,
                "week": self.current_week,
                "outstanding": outstanding,
            }

        recipient_index = (self.current_week - 1) % len(self.member_order)
        recipient_key = self.member_order[recipient_index]
        recipient = self.members[recipient_key]
        pot = self.weekly_contribution * len(self.member_order)
        week = self.current_week

        self.payout_history.append({
            "week": week,
            "recipient": recipient,
            "amount": pot,
        })
        self.current_week += 1
        for key in self.member_order:
            self.payments[key] = 0

        return {
            "closed": True,
            "week": week,
            "recipient": recipient,
            "amount": pot,
        }
