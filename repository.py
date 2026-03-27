import db
from datetime import datetime


class Customer:
    def __init__(self, id, name, rate):
        self.id = id
        self.name = name
        self.rate = rate
    
    def calculate_balance(self, transactions):
        balance = 0
        for tr in transactions:
            if tr.transaction_type.lower() == "charge":
                balance += tr.amount
            elif tr.transaction_type.lower() == "payment":
                balance -= tr.amount
        return balance

class Transaction:
    def __init__(self, id, customer_id, transaction_type, amount, date, notes):
        self.id = id # primary key for transactions
        self.customer_id = customer_id
        self.transaction_type = transaction_type # type: "Charge" or "Payment"
        self.amount = amount
        self.date = self._parse_date(date)
        self.notes = notes

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

def get_all_customers():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, name, rate FROM customers")
    rows = cursor.fetchall()
    return [Customer(row["id"], row["name"], row["rate"]) for row in rows]


def get_specific_customer(customer_id) -> Customer:
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, name, rate FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    if row:
        return Customer(row["id"], row["name"], row["rate"])
    
    # Else
    print(f"No customer found with ID {customer_id}.")
    return None

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
    cursor.execute("SELECT id, customer_id, transaction_type, amount, date, notes FROM transactions")
    rows = cursor.fetchall()
    return [Transaction(row["id"], row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"]) for row in rows]

def get_transactions_for_customer(customer_id):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, customer_id, transaction_type, amount, date, notes FROM transactions WHERE customer_id = ?", (customer_id,))
    rows = cursor.fetchall()
    return [Transaction(row["id"], row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"]) for row in rows]

def get_specific_transaction(transaction_id):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, customer_id, transaction_type, amount, date, notes FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    if row:
        return Transaction(row["id"], row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"])
    
    # Else
    print(f"No transaction found with ID {transaction_id}.")
    return None

def batch_insert_transactions(transactions: list):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.executemany(
        "INSERT INTO transactions (customer_id, transaction_type, amount, date, notes) VALUES (?, ?, ?, ?, ?)",
        [
            (t.customer_id, t.transaction_type, t.amount,
             t.date.strftime("%Y-%m-%d %H:%M:%S"), t.notes)
            for t in transactions
        ]
    )
    db_conn.commit()

def add_transaction(transaction: Transaction):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO transactions (customer_id, transaction_type, amount, date, notes) VALUES (?, ?, ?, ?, ?)", 
                   (transaction.customer_id, transaction.transaction_type, transaction.amount, transaction.date.strftime("%Y-%m-%d %H:%M:%S"), transaction.notes))
    db_conn.commit()