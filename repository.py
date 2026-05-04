import calendar
import db
from datetime import datetime


class Customer:
    def __init__(self, id, name, rate, is_active=1):
        self.id = id
        self.name = name
        self.rate = rate
        self.is_active = is_active
    
    def calculate_balance(self, transactions):
        balance = 0
        for tr in transactions:
            if tr.transaction_type.lower() == "charge":
                balance += tr.amount
            elif tr.transaction_type.lower() == "payment":
                balance -= tr.amount
        return balance

class Transaction:
    def __init__(self, id, customer_id, transaction_type, amount, date, notes, statement_month=None):
        self.id = id # primary key for transactions
        self.customer_id = customer_id
        self.transaction_type = transaction_type # type: "Charge" or "Payment"
        self.amount = amount
        self.date = self._parse_date(date)
        self.notes = notes
        self.statement_month = statement_month  # "YYYY-MM", set on payments to tag which month they pay for

    def _parse_date(self, date):
        if isinstance(date, datetime):
            return date
        if isinstance(date, str):
            try:
                return datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        raise TypeError("Invalid date type")

# ---- Customers ----
def create_customers_table():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            rate INTEGER
        )
        """)
    db_conn.commit()

def reset_customer_data():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS customers")
    create_customers_table()
    db_conn.commit()

def run_migrations():
    db_conn = db.get_db()
    try:
        db_conn.execute("ALTER TABLE customers ADD COLUMN is_active INTEGER DEFAULT 1")
        db_conn.commit()
    except Exception:
        pass  # column already exists
    try:
        db_conn.execute("ALTER TABLE transactions ADD COLUMN statement_month TEXT")
        db_conn.commit()
    except Exception:
        pass  # column already exists

def get_all_customers(active_only: bool = True):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    if active_only:
        cursor.execute("SELECT id, name, rate, is_active FROM customers WHERE is_active = 1")
    else:
        cursor.execute("SELECT id, name, rate, is_active FROM customers")
    rows = cursor.fetchall()
    return [Customer(row["id"], row["name"], row["rate"], row["is_active"]) for row in rows]

def get_specific_customer(customer_id) -> Customer:
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, name, rate, is_active FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    if row:
        return Customer(row["id"], row["name"], row["rate"], row["is_active"])
    print(f"No customer found with ID {customer_id}.")
    return None

def update_customer(customer_id: int, name: str, rate: float):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("UPDATE customers SET name=?, rate=? WHERE id=?", (name, rate, customer_id))
    db_conn.commit()

def deactivate_customer(customer_id: int):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("UPDATE customers SET is_active=0 WHERE id=?", (customer_id,))
    db_conn.commit()

def restore_customer(customer_id: int):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("UPDATE customers SET is_active=1 WHERE id=?", (customer_id,))
    db_conn.commit()

def get_all_balances():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT customer_id,
               SUM(CASE WHEN LOWER(transaction_type) = 'charge' THEN amount ELSE -amount END) as balance
        FROM transactions
        GROUP BY customer_id
    """)
    rows = cursor.fetchall()
    return {row["customer_id"]: row["balance"] for row in rows}

def add_customer(customer: Customer):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO customers (name, rate) VALUES (?, ?)", (customer.name, customer.rate))
    db_conn.commit()


# ---- Transactions ----
def create_transactions_table():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            transaction_type TEXT,
            amount INTEGER,
            date TEXT,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
        """)
    db_conn.commit()

def reset_transaction_data():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS transactions")
    create_transactions_table()
    db_conn.commit()

def get_all_transactions():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, customer_id, transaction_type, amount, date, notes, statement_month FROM transactions")
    rows = cursor.fetchall()
    return [Transaction(row["id"], row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"], row["statement_month"]) for row in rows]

def get_transactions_for_customer(customer_id):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, customer_id, transaction_type, amount, date, notes, statement_month FROM transactions WHERE customer_id = ?", (customer_id,))
    rows = cursor.fetchall()
    return [Transaction(row["id"], row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"], row["statement_month"]) for row in rows]

def get_specific_transaction(transaction_id):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, customer_id, transaction_type, amount, date, notes, statement_month FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    if row:
        return Transaction(row["id"], row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"], row["statement_month"])
    print(f"No transaction found with ID {transaction_id}.")
    return None

def batch_insert_transactions(transactions: list):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.executemany(
        "INSERT INTO transactions (customer_id, transaction_type, amount, date, notes, statement_month) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (t.customer_id, t.transaction_type, t.amount,
             t.date.strftime("%Y-%m-%d %H:%M:%S"), t.notes, t.statement_month)
            for t in transactions
        ]
    )
    db_conn.commit()

def delete_transaction(transaction_id: int):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))
    db_conn.commit()

def update_transaction(transaction_id: int, amount: float, date: str, notes: str):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE transactions SET amount=?, date=?, notes=? WHERE id=?",
        (amount, date, notes, transaction_id)
    )
    db_conn.commit()

def add_transaction(transaction: Transaction):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO transactions (customer_id, transaction_type, amount, date, notes, statement_month) VALUES (?, ?, ?, ?, ?, ?)",
                   (transaction.customer_id, transaction.transaction_type, transaction.amount, transaction.date.strftime("%Y-%m-%d %H:%M:%S"), transaction.notes, transaction.statement_month))
    db_conn.commit()

def get_statement_data(customer_id: int, year: int, month: int) -> dict:
    db_conn = db.get_db()
    cursor = db_conn.cursor()

    period_start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    period_end = f"{year}-{month:02d}-{last_day:02d}"

    cursor.execute("""
        SELECT SUM(CASE WHEN LOWER(transaction_type) = 'charge' THEN amount ELSE -amount END)
        FROM transactions
        WHERE customer_id = ? AND date < ?
    """, (customer_id, period_start))
    row = cursor.fetchone()
    starting_balance = row[0] or 0.0

    cursor.execute("""
        SELECT id, customer_id, transaction_type, amount, date, notes, statement_month
        FROM transactions
        WHERE customer_id = ? AND date >= ? AND date <= ?
        ORDER BY date
    """, (customer_id, period_start, period_end + " 23:59:59"))
    rows = cursor.fetchall()
    period_transactions = [
        Transaction(r["id"], r["customer_id"], r["transaction_type"], r["amount"], r["date"], r["notes"], r["statement_month"])
        for r in rows
    ]

    charges = [t for t in period_transactions if t.transaction_type.lower() == "charge"]
    payments = [t for t in period_transactions if t.transaction_type.lower() == "payment"]
    total_charges = sum(t.amount for t in charges)
    total_payments = sum(t.amount for t in payments)
    ending_balance = starting_balance + total_charges - total_payments

    return {
        "starting_balance": starting_balance,
        "charges": charges,
        "payments": payments,
        "total_charges": total_charges,
        "total_payments": total_payments,
        "ending_balance": ending_balance,
    }


def get_transaction_date_range():
    """Returns (min_date_str, max_date_str) or None if no transactions exist."""
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT MIN(date), MAX(date) FROM transactions")
    row = cursor.fetchone()
    if row[0] is None:
        return None
    return (row[0], row[1])


def get_months_with_monthly_charges():
    """Returns a set of (year, month) tuples that have at least one monthly charge transaction."""
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("""
        SELECT DISTINCT CAST(substr(date, 1, 4) AS INTEGER) AS y,
                        CAST(substr(date, 6, 2) AS INTEGER) AS m
        FROM transactions
        WHERE LOWER(notes) = 'monthly charge'
    """)
    return {(row["y"], row["m"]) for row in cursor.fetchall()}


def get_monthly_charge_statement(year: int, month: int) -> list:
    """Returns one dict per customer charged that month.

    Each dict: { 'customer': Customer, 'charge': Transaction, 'payments': [Transaction] }
    Payments are matched by statement_month='YYYY-MM' when set, falling back to
    payments whose date falls within the month for older records.
    """
    db_conn = db.get_db()
    cursor = db_conn.cursor()

    period_start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    period_end = f"{year}-{month:02d}-{last_day:02d} 23:59:59"
    month_str = f"{year}-{month:02d}"

    cursor.execute("""
        SELECT id, customer_id, transaction_type, amount, date, notes, statement_month
        FROM transactions
        WHERE LOWER(notes) = 'monthly charge' AND date >= ? AND date <= ?
        ORDER BY date
    """, (period_start, period_end))
    charge_rows = cursor.fetchall()

    if not charge_rows:
        return []

    customer_ids = list({row["customer_id"] for row in charge_rows})
    placeholders = ",".join("?" * len(customer_ids))

    # Payments tagged to this statement month, OR (legacy) payments whose date falls in the month
    cursor.execute(f"""
        SELECT id, customer_id, transaction_type, amount, date, notes, statement_month
        FROM transactions
        WHERE LOWER(transaction_type) = 'payment'
          AND customer_id IN ({placeholders})
          AND (statement_month = ? OR (statement_month IS NULL AND date >= ? AND date <= ?))
        ORDER BY date
    """, (*customer_ids, month_str, period_start, period_end))
    payment_rows = cursor.fetchall()

    payments_by_customer: dict = {}
    for row in payment_rows:
        cid = row["customer_id"]
        t = Transaction(row["id"], cid, row["transaction_type"], row["amount"], row["date"], row["notes"], row["statement_month"])
        payments_by_customer.setdefault(cid, []).append(t)

    cursor.execute(f"SELECT id, name, rate, is_active FROM customers WHERE id IN ({placeholders})", customer_ids)
    customers_by_id = {row["id"]: Customer(row["id"], row["name"], row["rate"], row["is_active"]) for row in cursor.fetchall()}

    result = []
    for row in charge_rows:
        cid = row["customer_id"]
        result.append({
            "customer": customers_by_id.get(cid),
            "charge": Transaction(row["id"], cid, row["transaction_type"], row["amount"], row["date"], row["notes"], row["statement_month"]),
            "payments": payments_by_customer.get(cid, []),
        })

    return result


def has_monthly_charges_for_month(year: int, month: int) -> int:
    """Returns the count of monthly charge transactions for the given month."""
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    period_start = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    period_end = f"{year}-{month:02d}-{last_day:02d} 23:59:59"
    cursor.execute("""
        SELECT COUNT(*) FROM transactions
        WHERE LOWER(notes) = 'monthly charge' AND date >= ? AND date <= ?
    """, (period_start, period_end))
    return cursor.fetchone()[0]