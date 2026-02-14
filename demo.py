from datetime import datetime

# DONE Use SQL to store transactions/ customers instead of in-memory lists
# TODO @implement balance caching and updating in Customer class
# DONE use datetime objects for dates instead of strings

import sqlite3

con = sqlite3.connect("demo-data2.db")
cur = con.cursor()


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



# ---- Customers ----
def create_customers_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            rate INTEGER
        )
        """)
    con.commit()

def get_all_customer_data() -> list[Customer]:
    # Returns list of Customer objects from SQL database
    sql_customer_data = cur.execute("SELECT id, name, rate FROM customers").fetchall()
    customers = [Customer(id, name, rate) for id, name, rate in sql_customer_data]
    return customers
def get_specific_customer_data(customer_id) -> Customer:
    sql_customer_data = cur.execute("SELECT id, name, rate FROM customers WHERE id = ?", (customer_id,)).fetchone()
    if sql_customer_data:
        return Customer(customer_id, sql_customer_data[1], sql_customer_data[2])
    print(f"No customer found with ID {customer_id}.")
    return None

def populate_customer_data(customer: Customer):
    cur.execute("INSERT INTO customers VALUES (?, ?, ?)", (customer.id, customer.name, customer.rate))
    con.commit()

def reset_customer_data():
    cur.execute("DROP TABLE IF EXISTS customers")
    create_customers_table()
    con.commit()


# ---- Transactions ----
def create_transactions_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            customer_id INTEGER,
            transaction_type TEXT,
            amount INTEGER,
            date TEXT,
            notes TEXT
        )
        """)
    con.commit()

def get_all_transaction_data() -> list[Transaction]:
    # Returns list of Transaction objects from SQL database
    sql_transaction_data = cur.execute("SELECT customer_id, transaction_type, amount, date, notes FROM transactions").fetchall()
    transactions = [Transaction(customer_id, transaction_type, amount, date, notes) for customer_id, transaction_type, amount, date, notes in sql_transaction_data]
    return transactions

def get_specific_transaction_data(customer_id) -> list[Transaction]:
    sql_transaction_data = cur.execute("SELECT customer_id, transaction_type, amount, date, notes FROM transactions WHERE customer_id = ?", (customer_id,)).fetchall()
    transactions = [Transaction(customer_id, transaction_type, amount, date, notes) for customer_id, transaction_type, amount, date, notes in sql_transaction_data]
    return transactions

def populate_transaction_data(transaction: Transaction):
    cur.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                (transaction.customer_id, transaction.transaction_type, transaction.amount, transaction.date, transaction.notes))
    con.commit()

def reset_transaction_data():
    cur.execute("DROP TABLE IF EXISTS transactions")
    create_transactions_table()
    con.commit()


class Ledger:
    def __init__(self):
        self.transactions = []
        self._refresh_transactions()
    
    def _refresh_transactions(self):
        self.transactions = get_all_transaction_data()
    
    def record_transaction(self, transaction):
        populate_transaction_data(transaction)
        self._refresh_transactions()

    def calculate_balance(self, customer_id):
        balance = 0
        for tr in self.transactions:
            if tr.customer_id == customer_id:
                if tr.transaction_type == "Charge":
                    balance += tr.amount
                elif tr.transaction_type == "Payment":
                    balance -= tr.amount
        return balance

class Displayer:
    def __init__(self, ledger):
        self.ledger = ledger

    def _sorted_transactions(self):
        return sorted(self.ledger.transactions, key=lambda x: x.date)

    def customers(self, customers):
        for c in customers:
            print(f"ID: {c.id}, Name: {c.name}, Rate: {c.rate}, Balance: {self.ledger.calculate_balance(c.id)}")

    def all_transactions(self):
        for tr in self._sorted_transactions():
            print(f"Customer ID: {tr.customer_id}, Transaction Type: {tr.transaction_type}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")

    def all_charges(self):
        for tr in self._sorted_transactions():
            if tr.transaction_type == "Charge":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")
    
    def all_payments(self):
        for tr in self._sorted_transactions():
            if tr.transaction_type == "Payment":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")

    def specific_transactions(self, customer_id):
        specific_transactions = get_specific_transaction_data(customer_id)
        for tr in sorted(specific_transactions, key=lambda x: x.date):
            print(f"Customer ID: {tr.customer_id}, Transaction Type: {tr.transaction_type}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")

    def specific_charges(self, customer_id):
        specific_transactions = get_specific_transaction_data(customer_id)
        for tr in sorted(specific_transactions, key=lambda x: x.date):
            if tr.transaction_type == "Charge":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")

    def specific_payments(self, customer_id):
        specific_transactions = get_specific_transaction_data(customer_id)
        for tr in sorted(specific_transactions, key=lambda x: x.date):
            if tr.transaction_type == "Payment":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")

# CLI
# First, put date
# options: 1) charge, 2) payment, 3) show customer(s), 4) show transactions, 5) show charges, 6) show payments
# For charges and payments, ask for customer id, amount, date, notes
# for options 3-6, ask for customer id (optional, if blank show all)

def cli(ledger, display):
    print("Welcome to the Customer Ledger CLI!")
    print("Please enter the date (YYYY-MM-DD) Enter for today:")
    date = input().strip()
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"Date set to {date}.")
    while True:
        print("Select an option:")
        print("0) Exit")
        print("1) Charge")
        print("1.2) Monthly Service Charge")
        print("2) Payment")
        print("3) Show Customers")
        print("4) Show Transactions")
        print("5) Show Charges")
        print("6) Show Payments")
        option = input().strip()
        if option == "0":
            print("Exiting CLI. Goodbye!")
            break
        if option == "1.2":
            customers = get_all_customer_data()
            for c in customers:
                transaction = Transaction(c.id, "Charge", c.rate, date, "Monthly Service Charge")
                ledger.record_transaction(transaction)
            print("Monthly service charges recorded for all customers.")
            continue
        if option in ["1", "2"]:
            print("Enter customer ID:")
            customer_id = int(input().strip())
            print("Enter amount:")
            amount = int(input().strip())
            print("Enter notes:")
            notes = input().strip()
            transaction_type = "Charge" if option == "1" else "Payment"
            transaction = Transaction(customer_id, transaction_type, amount, date, notes)
            ledger.record_transaction(transaction)
            print(f"{transaction_type} recorded for Customer ID {customer_id}.")
            continue
        
        print("Customer ID (press Enter to show all):")
        customer_id_input = input().strip()
        if option == "3":
            if customer_id_input:
                customer_id = int(customer_id_input)
                customer = get_specific_customer_data(customer_id)
                if customer:
                    display.customers([customer])
            else:
                customers = get_all_customer_data()
                display.customers(customers)

        elif option == "4":
            if customer_id_input:
                customer_id = int(customer_id_input)
                display.specific_transactions(customer_id)
            else:
                display.all_transactions()
        elif option == "5":
            if customer_id_input:
                customer_id = int(customer_id_input)
                display.specific_charges(customer_id)
            else:
                display.all_charges()
        elif option == "6":
            if customer_id_input:
                customer_id = int(customer_id_input)
                display.specific_payments(customer_id)
            else:
                display.all_payments()
        else:
            print("Invalid option. Please try again.")



def main():
    # reset_customer_data()
    # reset_transaction_data()    
    # ---- Setup customers ----
    # populate_customer_data(Customer(0, "Alex", 100))
    # populate_customer_data(Customer(1, "Samantha", 150))
    # populate_customer_data(Customer(2, "Greg", 175))

    customers = get_all_customer_data()

    # ---- Setup ledger and displayer ----
    ledger = Ledger()
    display = Displayer(ledger)
    cli(ledger, display)

    # print("=== Initial Customers ===")
    # display.customers(customers)

    # # ---- Monthly charges (2 months) ----
    # print("\n=== Charging Monthly Service ===")
    # for c in customers:
    #     ledger.record_transaction(Transaction(
    #         customer_id=c.id,
    #         transaction_type="Charge",
    #         amount=c.rate,
    #         date="2026-01-01",
    #         notes="Monthly service"
    #     ))
    #     ledger.record_transaction(Transaction(
    #         customer_id=c.id,
    #         transaction_type="Charge",
    #         amount=c.rate,
    #         date="2026-02-01",
    #         notes="Monthly service"
    #     ))

    # display.customers(customers)

    # # ---- Extra service charges ----
    # print("\n=== Adding Extra Charges ===")
    # ledger.record_transaction(Transaction(
    #                           customer_id=0,
    #                           transaction_type="Charge",
    #                           amount=50,
    #                           date="2026-02-10",
    #                           notes="Custom Design Work")
    #                         )
    
    # ledger.record_transaction(Transaction(
    #                           customer_id=1,
    #                           transaction_type="Charge",
    #                           amount=75,
    #                           date="2026-02-12",
    #                           notes="Additional Consulting")
    #                         )
    
    # display.customers(customers)

    # # ---- Record payments ----
    # print("\n=== Recording Payments ===")

    # ledger.record_transaction(Transaction(customer_id=1,
    #                             transaction_type="Payment",
    #                             amount=100,
    #                             date="2026-02-15",
    #                             notes="Credit Card")
    #                             )
    
    # ledger.record_transaction(Transaction(customer_id=2,
    #                             transaction_type="Payment",
    #                             amount=175,
    #                             date="2026-02-18",
    #                             notes="PayPal")
    #                             )

    # display.customers(customers)

    # # ---- Show charges ----
    # print("\n=== All Charges ===")
    # display.all_charges()

    # print("\n=== Charges for Customer 1 (Samantha) ===")
    # display.specific_charges(1)

    # # ---- Show payments ----
    # print("\n=== All Payments ===")
    # display.all_payments()

    # print("\n=== Payments for Customer 2 (Greg) ===")
    # display.specific_payments(2)

    # # ---- Ledger ----
    # print("\n=== Ledger (Chronological) ===")
    # display.all_transactions()

    # print("\n=== Final Customer Balances ===")
    # display.customers(customers)

    con.close()

if __name__ == "__main__":
    main()