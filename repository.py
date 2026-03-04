import db
from datetime import datetime


class Customer:
    def __init__(self, id, name, rate):
        self.id = id
        self.name = name
        self.rate = rate

class Transaction:
    def __init__(self, customer_id, transaction_type, amount, date, notes):
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

def get_all_transactions():
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT customer_id, transaction_type, amount, date, notes FROM transactions")
    rows = cursor.fetchall()
    return [Transaction(row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"]) for row in rows]

def get_transactions_for_customer(customer_id):
    db_conn = db.get_db()
    cursor = db_conn.cursor()
    cursor.execute("SELECT customer_id, transaction_type, amount, date, notes FROM transactions WHERE customer_id = ?", (customer_id,))
    rows = cursor.fetchall()
    return [Transaction(row["customer_id"], row["transaction_type"], row["amount"], row["date"], row["notes"]) for row in rows]

