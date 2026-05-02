# PaymentTracker

A Flask web application for managing customer payments, recurring charges, and AI-powered check processing. Designed for service providers who bill customers on a monthly basis and receive physical checks as payment.

## Features

- **Customer management** — Add customers with names and monthly service rates
- **Transaction tracking** — Record payments and charges with dates and notes
- **Balance calculation** — Real-time balance per customer (charges minus payments)
- **Monthly charges** — Bulk-add monthly service charges to all customers at once
- **AI check processing** — Upload check images or PDFs; Claude extracts payer, amount, date, and memo automatically
- **Check review workflow** — Review and edit AI-extracted check data before committing transactions
- **Transaction history** — Full history per customer and across all customers

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Python / Flask |
| Database | SQLite |
| Templating | Jinja2 |
| AI / OCR | Anthropic Claude API (`claude-sonnet-4-6`) |
| Environment | python-dotenv |

## Project Structure

```
PaymentTracker/
├── app.py                  # Flask routes and application entry point
├── db.py                   # SQLite connection management (per-request via Flask g)
├── repository.py           # Data models (Customer, Transaction) and DB operations
├── check_processor.py      # AI-powered check image/PDF data extraction
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── demo-data2.db           # SQLite database file (not committed)
├── static/
│   └── style.css           # Application styles
└── templates/
    ├── index.html          # Home page / navigation
    ├── customer_list.html  # All customers with balances
    ├── customer.html       # Individual customer detail and transactions
    ├── add_customer.html   # Add new customer form
    ├── transaction_list.html # All transactions
    ├── add_transaction.html  # Add transaction form
    ├── add_monthly_charges.html # Bulk monthly charge page
    ├── upload_checks.html  # Check upload interface
    └── review_checks.html  # Review and edit extracted check data
```

## Installation

**Prerequisites:** Python 3.x

```bash
git clone <repo-url>
cd PaymentTracker
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-api-key-here
```

The API key is required only for the check processing feature. The rest of the app works without it.

## Running the App

```bash
python app.py
```

Access the app at [http://localhost:5000](http://localhost:5000).

The SQLite database and tables are created automatically on first run.

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page with navigation links |
| `/customers` | GET | List all customers with current balances |
| `/customers/<id>` | GET | Customer detail with full transaction history |
| `/add_customer` | GET / POST | Add a new customer |
| `/transactions` | GET | List all transactions |
| `/add_transaction` | GET / POST | Manually record a payment or charge |
| `/add_monthly_charges` | GET / POST | Bulk-add monthly charges to all customers |
| `/process_checks` | GET / POST | Upload check images/PDFs for AI extraction |
| `/review_checks` | GET | Review and edit extracted check data |
| `/commit_checks` | POST | Save reviewed checks as transactions |

## Data Models

**Customer**

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Customer name |
| rate | INTEGER | Monthly service rate (dollars) |

**Transaction**

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary key |
| customer_id | INTEGER | Foreign key → customers.id |
| transaction_type | TEXT | `"Charge"` or `"Payment"` |
| amount | INTEGER | Dollar amount |
| date | TEXT | Date (YYYY-MM-DD) |
| notes | TEXT | Optional memo or notes |

**Balance formula:** `balance = SUM(charges) - SUM(payments)` per customer.

## Check Processing Workflow

1. **Upload** — Go to `/process_checks` and upload one or more check images (JPG, PNG) or PDFs.
2. **Extract** — The app sends the files to Claude, which reads each check and extracts:
   - Payer name
   - Amount
   - Check number
   - Date
   - Memo / notes
   - Matched customer ID (fuzzy name match against existing customers)
3. **Review** — Extracted data is shown at `/review_checks` for human verification and editing.
4. **Commit** — Submitting the review form saves each check as a `Payment` transaction in the database.
