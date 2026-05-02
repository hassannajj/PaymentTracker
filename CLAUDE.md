# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Engineering Standards

## Code Quality
- Use strong typing everywhere, never use `any`
- Write explicit error messages that explain what went wrong and what's expected
- Keep variable and function names descriptive and clear
- Remove unused code and dead imports aggressively

## Logging
- Log every significant action, state change, and error
- Logs should answer: what happened, where, and with what data

## Git
- Write commit messages that explain WHY something changed, not just what
- Every feature gets its own branch
- Use migration files for all database changes, never edit schema directly

## Security
- Never hardcode secrets, always use env vars
- Use read-only database users for debugging
- Scope credentials to minimum necessary permissions

## General
- Plan before implementing — clarify requirements first
- When something breaks, find a way to give the AI access to fix it rather than fixing manually



## Running the app

```bash
flask run
```

Requires `ANTHROPIC_API_KEY` in the environment (used by `check_processor.py`). Create a `.env` file — `python-dotenv` is installed and Flask will pick it up automatically.

The SQLite database file is `demo-data2.db` in the project root.

## Architecture

The app is a Flask web app with a clean layer separation:

- **`db.py`** — SQLite connection manager using Flask's `g` object. One connection per request, closed in `app.teardown_appcontext`. All other modules call `db.get_db()`.
- **`repository.py`** — All database access lives here. Defines the `Customer` and `Transaction` dataclasses (plain Python classes, not ORM models) and all SQL queries. `Customer.calculate_balance()` iterates transactions in Python; `get_all_balances()` does it in a single SQL query for the list view.
- **`check_processor.py`** — Sends uploaded check images/PDFs to the Claude API (via `anthropic` SDK) as base64-encoded content. Returns a list of dicts with extracted fields (`payer_name`, `customer_id`, `amount`, `check_number`, `date`, `memo`, `notes`). Claude fuzzy-matches payer names to the customer list passed in.
- **`app.py`** — Flask routes only. No business logic — just calls `repository.*` and `check_processor.*`, passes data to templates.
- **`demo.py`** — Legacy CLI script (pre-web). Contains `Ledger` and `Displayer` classes. Not used by the Flask app; ignore for web development.
- **`test.py`** — Scratch script that resets and repopulates the DB with test data. Running it **wipes `demo-data2.db`**.

## Check ingestion flow

1. `POST /process_checks` — receives uploaded files, calls `check_processor.extract_checks_from_files()`, stores the result in `session['pending_checks']`
2. `GET /review_checks` — renders extracted checks as an editable form for user review
3. `POST /commit_checks` — reads the reviewed form data and calls `repository.batch_insert_transactions()`

## Transaction types

Only two values are used throughout: `"Charge"` and `"Payment"`. Balance = sum of charges − sum of payments. These are compared case-insensitively in `Customer.calculate_balance()` but stored with title case everywhere else.

## Known incomplete code

`app.py:99–103` — the `manual_check` branch inside `POST /process_checks` has no body (syntax error / placeholder). Do not run the app without addressing this first.
