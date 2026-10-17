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

    def report(self):
        members = []
        for key in self.member_order:
            paid = self.payments[key]
            owed = self.remaining_this_week(key)
            if owed == 0:
                status = "PAID IN FULL"
            elif paid == 0:
                status = "NOT PAID"
            else:
                status = "PARTIALLY PAID"
            members.append({
                "name": self.members[key],
                "paid": paid,
                "owes": owed,
                "status": status,
            })

        return {
            "weekly_contribution": self.weekly_contribution,
            "current_week": self.current_week,
            "members": members,
            "collected": sum(self.payments.values()),
            "expected_pot": len(self.member_order) * self.weekly_contribution,
            "payout_history": list(self.payout_history),
        }


def print_close_result(result):
    if not result["closed"]:
        print(f"\nWeek {result['week']} cannot close.")
        print("No payout has been made.")
        print("Outstanding contributions:")
        for item in result["outstanding"]:
            print(f"  {item['name']}: owes {format_money(item['owes'])}")
        return

    print(f"\nWeek {result['week']} closed successfully.")
    print(f"Payout recipient: {result['recipient']}")
    print(f"Pot paid: {format_money(result['amount'])}")


def print_report(data):
    print("\n========== SUSU REPORT ==========")
    print(f"Weekly contribution: {format_money(data['weekly_contribution'])}")
    print(f"Current week: {data['current_week']}")
    print(f"Number of members: {len(data['members'])}")
    print("\nMember contributions for the current week:")
    if not data["members"]:
        print("  No members have been added.")
    for member in data["members"]:
        print(
            f"  {member['name']}: "
            f"paid {format_money(member['paid'])}, "
            f"owes {format_money(member['owes'])} "
            f"({member['status']})"
        )
    print(f"\nCollected this week: {format_money(data['collected'])}")
    print(f"Expected pot: {format_money(data['expected_pot'])}")
    print("\nPayout history:")
    if not data["payout_history"]:
        print("  No payouts have been made.")
    for payout in data["payout_history"]:
        print(
            f"  Week {payout['week']}: "
            f"{payout['recipient']} received "
            f"{format_money(payout['amount'])}"
        )
    print("=================================")


def main():
    print("=== SUSU GROUP MANAGER ===")
    while True:
        try:
            weekly_amount = parse_money(
                input("Enter weekly contribution in GHS (e.g. 50.00): ")
            )
            break
        except ValueError as error:
            print(f"Error: {error}")

    group = SusuGroup(weekly_amount)

    while True:
        print(
            "\n--- MENU ---\n"
            "1. Add member\n"
            "2. Record contribution\n"
            "3. Close current week\n"
            "4. Show report\n"
            "5. Exit"
        )
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                name = group.add_member(input("Enter member name or ID: "))
                print(f"Added member: {name}")
            elif choice == "2":
                name = input("Enter member name or ID: ")
                amount = parse_money(input("Enter amount paid in GHS: "))
                recorded = group.record_contribution(name, amount)
                print(
                    f"Recorded {format_money(recorded['paid'])} for "
                    f"{recorded['name']}, week {recorded['week']}. "
                    f"Total paid: {format_money(recorded['total_paid'])}."
                )
            elif choice == "3":
                print_close_result(group.close_week())
            elif choice == "4":
                print_report(group.report())
            elif choice == "5":
                print("Goodbye.")
                break
            else:
                print("Invalid option. Choose 1 to 5.")
        except ValueError as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    main()

