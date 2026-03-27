from flask import Flask, request, render_template, redirect, url_for, session, flash
from markupsafe import escape
from datetime import datetime

import demo
import db
import repository
import check_processor


app = Flask(__name__)
app.secret_key = 'dev-secret-change-in-production'


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

@app.route('/process_checks', methods=['GET'])
def process_checks_form():
    return render_template('upload_checks.html')

@app.route('/process_checks', methods=['POST'])
def process_checks():
    files = request.files.getlist('checks')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected.')
        return redirect(url_for('process_checks_form'))
    customers = repository.get_all_customers()
    try:
        extracted = check_processor.extract_checks_from_files(files, customers)
    except Exception as e:
        flash(f'Error processing checks: {e}')
        return redirect(url_for('process_checks_form'))
    session['pending_checks'] = extracted
    return redirect(url_for('review_checks'))

@app.route('/review_checks')
def review_checks():
    pending = session.get('pending_checks', [])
    if not pending:
        return redirect(url_for('process_checks_form'))
    customers = repository.get_all_customers()
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('review_checks.html', checks=pending, customers=customers, today=today)

@app.route('/commit_checks', methods=['POST'])
def commit_checks():
    transactions = []
    index = 0
    while f'customer_id_{index}' in request.form:
        if request.form.get(f'delete_{index}') != 'on':
            t = repository.Transaction(
                id=None,
                customer_id=int(request.form[f'customer_id_{index}']),
                transaction_type='Payment',
                amount=float(request.form[f'amount_{index}']),
                date=request.form[f'date_{index}'],
                notes=request.form.get(f'notes_{index}', '')
            )
            transactions.append(t)
        index += 1
    if transactions:
        repository.batch_insert_transactions(transactions)
    session.pop('pending_checks', None)
    return redirect(url_for('show_transactions'))

@app.route('/add_monthly_charges', methods=['POST', 'GET'])
def add_monthly_charges():
    if request.method == 'POST':
        date = request.form.get('date')
        customers = repository.get_all_customers()
        for customer in customers:
            transaction = repository.Transaction(
                id=None,
                customer_id=customer.id,
                transaction_type="Charge",
                amount=customer.rate,
                date=date,
                notes="Monthly charge"
            )
            repository.add_transaction(transaction)
        return redirect(url_for('show_transactions'))

    # Else, GET request
    return render_template('add_monthly_charges.html')