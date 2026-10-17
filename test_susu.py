
import unittest

# Import the Susu system we want to test.
# These functions and the class should be defined in susu.py.
from susu import SusuGroup, format_money, parse_money


def group_with_members(*names, weekly="50.00"):
    """
    Helper function that creates a Susu group and adds members.

    *names allows us to pass any number of member names.
    weekly sets the weekly contribution amount as a string.

    Example:
        group_with_members("Ama", "Kofi", "Esi")
    """
    # Convert the contribution from cedis to pesewas.
    group = SusuGroup(parse_money(weekly))

    # Add every supplied name to the group.
    for name in names:
        group.add_member(name)

    # Return the prepared group for use in a test.
    return group


class ParseMoneyTests(unittest.TestCase):
    """Tests for converting and validating money amounts."""

    def test_parses_cedis_to_pesewas_exactly(self):
        # GH₵50.00 should become 5,000 pesewas.
        self.assertEqual(parse_money("50.00"), 5000)

        # GH₵12.50 should become 1,250 pesewas.
        self.assertEqual(parse_money("12.5"), 1250)

        # 15,000 pesewas should display as GH₵150.00.
        self.assertEqual(format_money(15000), "GHS 150.00")

    def test_rejects_zero_and_negative_amounts(self):
        # A contribution of zero must raise a ValueError.
        with self.assertRaises(ValueError):
            parse_money("0")

        # Negative contributions must also be rejected.
        with self.assertRaises(ValueError):
            parse_money("-10.00")

        # A Susu group cannot have a zero weekly contribution.
        with self.assertRaises(ValueError):
            SusuGroup(0)


class MemberAndPaymentValidationTests(unittest.TestCase):
    """Tests for member registration and contribution rules."""

    def test_rejects_duplicate_and_unknown_members(self):
        # Create a group containing only Ama.
        group = group_with_members("Ama")

        # Names are expected to be checked without case sensitivity.
        # Therefore, "ama" should be treated as a duplicate of "Ama".
        with self.assertRaises(ValueError):
            group.add_member("ama")

        # Kofi is not a registered member, so his payment must fail.
        with self.assertRaises(ValueError):
            group.record_contribution(
                "Kofi", parse_money("50.00")
            )

    def test_partial_payment_is_allowed(self):
        # Create a group with Esi as its only member.
        group = group_with_members("Esi")

        # Esi pays GH₵30 out of the required GH₵50.
        recorded = group.record_contribution(
            "Esi", parse_money("30.00")
        )

        # Check the amount Esi has paid, in pesewas.
        self.assertEqual(recorded["total_paid"], 3000)

        # Esi still owes GH₵20, or 2,000 pesewas.
        self.assertEqual(recorded["owes"], 2000)

        # The report should identify Esi as partially paid.
        self.assertEqual(
            group.report()["members"][0]["status"],
            "PARTIALLY PAID"
        )

    def test_rejects_payment_above_what_is_owed(self):
        # Ama owes GH₵50 at the beginning of the week.
        group = group_with_members("Ama")

        # Ama pays GH₵40, leaving GH₵10 outstanding.
        group.record_contribution("Ama", parse_money("40.00"))

        # An additional GH₵20 would exceed the outstanding balance.
        with self.assertRaises(ValueError):
            group.record_contribution("Ama", parse_money("20.00"))


class CloseWeekTests(unittest.TestCase):
    """Tests for weekly closing, payouts and reports."""

    def test_week_cannot_close_while_someone_owes(self):
        # Create a group with three members.
        group = group_with_members("Ama", "Kofi", "Esi")

        # Ama and Kofi pay in full; Esi pays only GH₵30.
        group.record_contribution("Ama", parse_money("50.00"))
        group.record_contribution("Kofi", parse_money("50.00"))
        group.record_contribution("Esi", parse_money("30.00"))

        # Attempt to close the week while Esi still owes GH₵20.
        result = group.close_week()

        # The week must remain open.
        self.assertFalse(result["closed"])

        # The current week must still be week 1.
        self.assertEqual(result["week"], 1)

        # Only Esi should appear in the outstanding balance list.
        self.assertEqual(
            result["outstanding"],
            [{"name": "Esi", "owes": 2000}]
        )

        # No progression to week 2 should occur.
        self.assertEqual(group.current_week, 1)

        # No payout should be added to the history.
        self.assertEqual(group.payout_history, [])

    def test_example_payout_then_next_recipient(self):
        # Create a group with three members.
        group = group_with_members("Ama", "Kofi", "Esi")

        # Record contributions for week 1.
        group.record_contribution("Ama", parse_money("50.00"))
        group.record_contribution("Kofi", parse_money("50.00"))
        group.record_contribution("Esi", parse_money("30.00"))

        # Closing must fail because Esi still owes GH₵20.
        self.assertFalse(group.close_week()["closed"])

        # Esi pays the remaining GH₵20.
        group.record_contribution("Esi", parse_money("20.00"))

        # All members have now paid GH₵50 each.
        closed = group.close_week()

        # Confirm that week 1 closed successfully.
        self.assertTrue(closed["closed"])

        # Ama is the first recipient in the payout rotation.
        self.assertEqual(closed["recipient"], "Ama")

        # Three contributions of GH₵50 produce GH₵150.
        self.assertEqual(closed["amount"], 15000)

        # The system should advance to week 2.
        self.assertEqual(group.current_week, 2)

        # All members contribute GH₵50 for week 2.
        for name in ("Ama", "Kofi", "Esi"):
            group.record_contribution(name, parse_money("50.00"))

        # Close week 2 after everyone has paid.
        week_two = group.close_week()

        # Kofi should be the next recipient.
        self.assertEqual(week_two["recipient"], "Kofi")

        # The payout remains GH₵150.
        self.assertEqual(week_two["amount"], 15000)

    def test_report_lists_paid_owing_and_history(self):
        # Create a group with Ama and Kofi.
        group = group_with_members("Ama", "Kofi")

        # Ama pays the full GH₵50 contribution.
        group.record_contribution("Ama", parse_money("50.00"))

        # Retrieve the current state of the group.
        data = group.report()

        # The report should show week 1 as the current week.
        self.assertEqual(data["current_week"], 1)

        # Ama should be marked as fully paid.
        self.assertEqual(
            data["members"][0]["status"], "PAID IN FULL"
        )

        # Kofi has not paid and therefore owes GH₵50.
        self.assertEqual(data["members"][1]["owes"], 5000)

        # There have been no completed payouts yet.
        self.assertEqual(data["payout_history"], [])

        # Kofi pays his full contribution.
        group.record_contribution("Kofi", parse_money("50.00"))

        # Close the week and pay the first recipient.
        group.close_week()

        # Retrieve the payout history from the updated report.
        history = group.report()["payout_history"]

        # Ama should appear as the first recipient.
        self.assertEqual(history[0]["recipient"], "Ama")

        # The group collected GH₵100 from its two members.
        self.assertEqual(history[0]["amount"], 10000)


# Run the tests when this file is executed directly.
# This does not run automatically when the file is imported.
if __name__ == "__main__":
    unittest.main()
