# TODO

- Maybe when showing the rate of a customer's statement, show the rate at the time of the statement rather than the customer's rate right now

## High Priority
- [x] Statement generation — per-customer statement view showing period, starting balance, charges, payments, ending balance
- [x] DB auto-initialization on first run — tables are not created automatically after removing demo.py/test.py
- [ ] Sort transactions chronologically on both the transactions page and customer profile page

## UI / Navigation
- [x] Navbar — currently every page requires going back to home to navigate
- [ ] Fix date display — some pages show full datetime string (2024-01-01 00:00:00) instead of just the date

## Data / Backend
- [ ] `amount` column is typed INTEGER in the DB schema but treated as float in Python — should be REAL
- [ ] Guard against adding monthly charges more than once in the same month
- [ ] Save per-customer monthly charge exclusions so deselections persist across sessions
- [ ] Editable customer fields (name, rate)

## Future Features
- [ ] Dashboard — total customers, how many paid this month, how many haven't, total income
- [ ] Mark customers active / inactive
- [ ] Stats page — average monthly rate, total income, etc.
- [ ] Add charges to multiple specific customers at once (for one-off extras like filter, chlorine, repairs)

## Security / Config
- [ ] Move `secret_key` in app.py out of source code and into .env
