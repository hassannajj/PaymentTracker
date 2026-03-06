from datetime import datetime
from repository import *
import db

# TODO @implement balance caching and updating in Customer class

import sqlite3


# Contains all transactions
class Ledger:
    def __init__(self):
        self.transactions = []
        self._refresh_transactions()
    
    def _refresh_transactions(self):
        self.transactions = get_all_transactions()
    
    def record_transaction(self, transaction):
        add_transaction(transaction)
        self._refresh_transactions()

    # TODO: Maybe optimize this by caching balances in Customer table and updating on each transaction instead of calculating from scratch each time
    # For now, this is simpler and good enough for demo purposes, but if we had a large number of transactions this could get slow
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
        print()

    def all_transactions(self):
        for tr in self._sorted_transactions():
            print(f"Customer ID: {tr.customer_id}, Transaction Type: {tr.transaction_type}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")
        print()

    def all_charges(self):
        for tr in self._sorted_transactions():
            if tr.transaction_type == "Charge":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")
        print()

    def all_payments(self):
        for tr in self._sorted_transactions():
            if tr.transaction_type == "Payment":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")
        print()

    def specific_transactions(self, customer_id):
        specific_transactions = get_specific_transaction(customer_id)
        for tr in sorted(specific_transactions, key=lambda x: x.date):
            print(f"Customer ID: {tr.customer_id}, Transaction Type: {tr.transaction_type}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")
        print()

    def specific_charges(self, customer_id):
        specific_transactions = get_specific_transaction(customer_id)
        for tr in sorted(specific_transactions, key=lambda x: x.date):
            if tr.transaction_type == "Charge":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")
        print()

    def specific_payments(self, customer_id):
        specific_transactions = get_specific_transaction_data(customer_id)
        for tr in sorted(specific_transactions, key=lambda x: x.date):
            if tr.transaction_type == "Payment":
                print(f"Customer ID: {tr.customer_id}, Amount: {tr.amount}, Date: {tr.date}, Notes: {tr.notes}")
        print()

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
        print("A) Add Customer")
        print("M) Monthly Service Charge")
        print("1) Charge")
        print("2) Payment")
        print("3) Show Customers")
        print("4) Show Transactions")
        print("5) Show Charges")
        print("6) Show Payments")
        option = input().strip()
        if option == "0":
            print("Exiting CLI. Goodbye!")
            break
        if option == "A":
            print("Enter new customer ID:")
            if not input().strip():
                print("Customer ID cannot be blank.")
                continue
            customer_id = int(input().strip())
            print("Enter new customer name:")
            name = input().strip()
            print("Enter new customer monthly rate:")
            rate = int(input().strip())
            new_customer = Customer(customer_id, name, rate)
            add_customer(new_customer)
            print(f"Customer {name} added with ID {customer_id} and monthly rate {rate}.")
            continue
        if option == "M":
            customers = add_customer()
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
                customer = get_specific_customer(customer_id)
                if customer:
                    display.customers([customer])
            else:
                customers = get_all_customers()
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
    reset_customer_data()
    reset_transaction_data()    
    # ---- Setup customers ----
    add_customer(Customer(0, "Alex", 100))
    add_customer(Customer(1, "Samantha", 150))
    add_customer(Customer(2, "Greg", 175))

    #customers = get_all_customer_data()

    # ---- Setup ledger and displayer ----
    ledger = Ledger()
    display = Displayer(ledger)
    cli(ledger, display)

    db.close_db()

if __name__ == "__main__":
    main()