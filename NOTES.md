# Notes

## Assumptions

- One process manages one susu group. Creating the group starts week 1 with a fixed weekly contribution that never changes.
- Member identity is a unique name or ID, compared case-insensitively (`Ama` and `ama` are the same person). Display names keep the spelling used when the member was added.
- Members may be added only before any contribution is recorded. After the first payment, the roster is locked. That keeps joining order, pot size, and payout rotation stable once money is in play.
- Contributions apply only to the current open week. There are no arrears from previous weeks because a week cannot close until everyone has paid in full.
- Partial payments are allowed and stack until the weekly amount is reached. A payment that would take a member over what they still owe for the current week is rejected.
- Payout order is joining order, cycling with modulo: week 1 pays member 1, week 2 pays member 2, and after the last member the rotation starts again.
- A week cannot be closed if the group has no members.
- Money is stored as integer pesewas (GHS × 100). Display always uses two decimal places. Amounts with more than two decimal places are rejected.

## Decisions

- Domain methods return data; the CLI prints. Tests assert on return values rather than menu output.
- Validation errors raise `ValueError` with a short message. The menu catches those errors so a bad input does not exit the program.
- `Decimal` is used only when parsing user input. After conversion to pesewas, all arithmetic is integer addition and multiplication.
- Overpayment is checked against the remaining balance for the week, not against the original weekly amount, so two partial payments cannot exceed the weekly contribution.

## What I would improve with more time

- Persist the group to a file so closing the program does not lose state.
- Support more than one group, and named groups.
- Record a contribution ledger (who paid, when, and how much) instead of only the current-week totals.
- Add an explicit “who is next to receive the pot” field on the report.
- Allow an administrator to reverse a mistaken payment before the week closes.
