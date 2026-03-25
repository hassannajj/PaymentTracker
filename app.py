from flask import Flask, request, render_template, redirect, url_for
from markupsafe import escape

import demo
import db
import repository


app = Flask(__name__)


@app.teardown_appcontext
def close_connection(exception):
    db.close_db()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/customers')
def show_customers():
    customers = repository.get_all_customers()
    balances = repository.get_all_balances()
    return render_template('customer_list.html', customers=customers, balances=balances)

@app.route('/customers/<int:id>')
def show_customer(id: int):
    customer = repository.get_specific_customer(id)
    if not customer:
        return {"error": f"No customer found with ID {id}"}, 404
    transactions = repository.get_transactions_for_customer(id)
    balance = customer.calculate_balance(transactions=transactions)
    return render_template('customer.html', customer=customer, transactions=transactions, balance=balance)

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        rate = request.form.get('rate')
        customer = repository.Customer(
            id=None,
            name=name,
            rate=rate
        )
        repository.add_customer(customer)
        return redirect(url_for('show_customers'))
    
    # Else, GET request
    return render_template('add_customer.html')


@app.route('/transactions')
def show_transactions():
    transactions = repository.get_all_transactions()
    return render_template('transaction_list.html', transactions=transactions)

@app.route('/transactions/<int:id>')
def show_transaction(id: int):
    transaction = repository.get_specific_transaction(id)
    if not transaction:
        return {"error": f"No transaction found with ID {id}"}, 404
    return f'Transaction {transaction.id}: Customer {transaction.customer_id} {transaction.transaction_type} {transaction.amount} on {transaction.date} ({transaction.notes})'

@app.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        transaction_type = request.form.get('transaction_type')
        amount = request.form.get('amount')
        date = request.form.get('date')
        notes = request.form.get('notes')
        transaction = repository.Transaction(
            id=None,
            customer_id=customer_id,
            transaction_type=transaction_type,
            amount=amount,
            date=date,
            notes=notes
        )        
        repository.add_transaction(transaction)
        return redirect(url_for('show_transactions'))

    # Else, GET request
    customers = repository.get_all_customers()
    return render_template('add_transaction.html', customers=customers)
