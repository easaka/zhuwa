import unittest

from susu import SusuGroup, format_money, parse_money


def group_with_members(*names, weekly="50.00"):
    group = SusuGroup(parse_money(weekly))
    for name in names:
        group.add_member(name)
    return group


class ParseMoneyTests(unittest.TestCase):
    def test_parses_cedis_to_pesewas_exactly(self):
        self.assertEqual(parse_money("50.00"), 5000)
        self.assertEqual(parse_money("12.5"), 1250)
        self.assertEqual(format_money(15000), "GHS 150.00")

    def test_rejects_zero_and_negative_amounts(self):
        with self.assertRaises(ValueError):
            parse_money("0")
        with self.assertRaises(ValueError):
            parse_money("-10.00")
        with self.assertRaises(ValueError):
            SusuGroup(0)


class MemberAndPaymentValidationTests(unittest.TestCase):
    def test_rejects_duplicate_and_unknown_members(self):
        group = group_with_members("Ama")
        with self.assertRaises(ValueError):
            group.add_member("ama")
        with self.assertRaises(ValueError):
            group.record_contribution("Kofi", parse_money("50.00"))

    def test_partial_payment_is_allowed(self):
        group = group_with_members("Esi")
        recorded = group.record_contribution("Esi", parse_money("30.00"))
        self.assertEqual(recorded["total_paid"], 3000)
        self.assertEqual(recorded["owes"], 2000)
        self.assertEqual(group.report()["members"][0]["status"], "PARTIALLY PAID")

    def test_rejects_payment_above_what_is_owed(self):
        group = group_with_members("Ama")
        group.record_contribution("Ama", parse_money("40.00"))
        with self.assertRaises(ValueError):
            group.record_contribution("Ama", parse_money("20.00"))


class CloseWeekTests(unittest.TestCase):
    def test_week_cannot_close_while_someone_owes(self):
        group = group_with_members("Ama", "Kofi", "Esi")
        group.record_contribution("Ama", parse_money("50.00"))
        group.record_contribution("Kofi", parse_money("50.00"))
        group.record_contribution("Esi", parse_money("30.00"))

        result = group.close_week()
        self.assertFalse(result["closed"])
        self.assertEqual(result["week"], 1)
        self.assertEqual(result["outstanding"], [{"name": "Esi", "owes": 2000}])
        self.assertEqual(group.current_week, 1)
        self.assertEqual(group.payout_history, [])

    def test_example_payout_then_next_recipient(self):
        group = group_with_members("Ama", "Kofi", "Esi")
        group.record_contribution("Ama", parse_money("50.00"))
        group.record_contribution("Kofi", parse_money("50.00"))
        group.record_contribution("Esi", parse_money("30.00"))
        self.assertFalse(group.close_week()["closed"])

        group.record_contribution("Esi", parse_money("20.00"))
        closed = group.close_week()
        self.assertTrue(closed["closed"])
        self.assertEqual(closed["recipient"], "Ama")
        self.assertEqual(closed["amount"], 15000)
        self.assertEqual(group.current_week, 2)

        for name in ("Ama", "Kofi", "Esi"):
            group.record_contribution(name, parse_money("50.00"))
        week_two = group.close_week()
        self.assertEqual(week_two["recipient"], "Kofi")
        self.assertEqual(week_two["amount"], 15000)

    def test_report_lists_paid_owing_and_history(self):
        group = group_with_members("Ama", "Kofi")
        group.record_contribution("Ama", parse_money("50.00"))
        data = group.report()
        self.assertEqual(data["current_week"], 1)
        self.assertEqual(data["members"][0]["status"], "PAID IN FULL")
        self.assertEqual(data["members"][1]["owes"], 5000)
        self.assertEqual(data["payout_history"], [])

        group.record_contribution("Kofi", parse_money("50.00"))
        group.close_week()
        history = group.report()["payout_history"]
        self.assertEqual(history[0]["recipient"], "Ama")
        self.assertEqual(history[0]["amount"], 10000)


if __name__ == "__main__":
    unittest.main()
