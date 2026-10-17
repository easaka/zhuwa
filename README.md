# Susu Group Manager

A command-line program that manages one rotating savings group (susu).

Each member pays the same fixed amount every week. When a week closes with every member paid in full, the whole pot is paid to the next member in joining order.

## Requirements

- Python 3.9 or later
- No third-party packages

## How to run the program

From the repository root:

```bash
python susu.py
```

Then use the menu:

1. Add member
2. Record contribution
3. Close current week
4. Show report
5. Exit

Amounts are entered in GHS, for example `50.00` or `12.50`.

### Example from the assignment

Weekly amount `50.00`, members Ama, Kofi, and Esi:

1. Add the three members.
2. Record `50.00` for Ama and Kofi, and `30.00` for Esi.
3. Close the week — it stays open and reports that Esi owes `GHS 20.00`.
4. Record `20.00` for Esi and close again — Ama receives `GHS 150.00`.
5. Week 2 begins; Kofi is next in line.

## How to run the tests

From the repository root:

```bash
python -m unittest test_susu.py -v
```

There are eight tests, including partial payments and a week that cannot close while someone still owes.
