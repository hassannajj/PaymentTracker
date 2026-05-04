from flask import Flask, request, render_template, redirect, url_for, session, flash
from markupsafe import escape
from datetime import datetime, date
import calendar as cal_module
import os

import db
import repository
import check_processor


app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-in-production')

with app.app_context():
    repository.create_customers_table()
    repository.create_transactions_table()
    repository.run_migrations()


@app.teardown_appcontext
def close_connection(exception):
    db.close_db()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/customers')
def show_customers():
    customers = repository.get_all_customers(active_only=True)
    inactive_customers = repository.get_all_customers(active_only=False)
    inactive_customers = [c for c in inactive_customers if not c.is_active]
    balances = repository.get_all_balances()
    return render_template('customer_list.html', customers=customers,
                           inactive_customers=inactive_customers, balances=balances)

@app.route('/customers/<int:id>')
def show_customer(id: int):
    customer = repository.get_specific_customer(id)
    if not customer:
        return {"error": f"No customer found with ID {id}"}, 404
    transactions = repository.get_transactions_for_customer(id)
    balance = customer.calculate_balance(transactions=transactions)
    return render_template('customer.html', customer=customer, transactions=transactions, balance=balance)

@app.route('/customers/<int:id>', methods=['PATCH'])
def update_customer(id: int):
    customer = repository.get_specific_customer(id)
    if not customer:
        return {"error": f"No customer found with ID {id}"}, 404
    data = request.get_json()
    try:
        name = data['name'].strip()
        rate = float(data['rate'])
    except (KeyError, ValueError) as e:
        return {"error": f"Invalid data: {e}"}, 400
    if not name:
        return {"error": "Name cannot be empty"}, 400
    repository.update_customer(id, name, rate)
    return {"id": id, "name": name, "rate": rate}

@app.route('/customers/<int:id>', methods=['DELETE'])
def deactivate_customer(id: int):
    customer = repository.get_specific_customer(id)
    if not customer:
        return {"error": f"No customer found with ID {id}"}, 404
    repository.deactivate_customer(id)
    return {}, 204

@app.route('/customers/<int:id>/restore', methods=['POST'])
def restore_customer(id: int):
    customer = repository.get_specific_customer(id)
    if not customer:
        return {"error": f"No customer found with ID {id}"}, 404
    repository.restore_customer(id)
    return {}, 204

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


def _iter_months(min_date_str: str, max_date_str: str):
    """Yield (year, month) tuples from min to max date inclusive, one per month."""
    y, m = int(min_date_str[:4]), int(min_date_str[5:7])
    max_y, max_m = int(max_date_str[:4]), int(max_date_str[5:7])
    while (y, m) <= (max_y, max_m):
        yield (y, m)
        m += 1
        if m > 12:
            m = 1
            y += 1


@app.route('/transactions')
def show_transactions():
    transactions = repository.get_all_transactions()
    date_range = repository.get_transaction_date_range()
    months = []
    if date_range:
        charged_months = repository.get_months_with_monthly_charges()
        months = [
            {
                "year": y, "month": m,
                "label": f"{cal_module.month_name[m]} {y}",
                "has_monthly_charge": (y, m) in charged_months,
            }
            for (y, m) in _iter_months(date_range[0], date_range[1])
        ]
        months.reverse()  # newest first
    customers = repository.get_all_customers(active_only=False)
    customers_by_id = {c.id: c.name for c in customers}
    return render_template('transaction_list.html', transactions=transactions, months=months,
                           customers_by_id=customers_by_id)

@app.route('/transactions/<int:id>')
def show_transaction(id: int):
    transaction = repository.get_specific_transaction(id)
    if not transaction:
        return {"error": f"No transaction found with ID {id}"}, 404
    return f'Transaction {transaction.id}: Customer {transaction.customer_id} {transaction.transaction_type} {transaction.amount} on {transaction.date} ({transaction.notes})'

@app.route('/transactions/<int:id>', methods=['DELETE'])
def delete_transaction(id: int):
    transaction = repository.get_specific_transaction(id)
    if not transaction:
        return {"error": f"No transaction found with ID {id}"}, 404
    repository.delete_transaction(id)
    return {}, 204

@app.route('/transactions/<int:id>', methods=['PATCH'])
def update_transaction(id: int):
    transaction = repository.get_specific_transaction(id)
    if not transaction:
        return {"error": f"No transaction found with ID {id}"}, 404
    data = request.get_json()
    try:
        amount = float(data['amount'])
        date = data['date']
        notes = data.get('notes', '')
    except (KeyError, ValueError) as e:
        return {"error": f"Invalid data: {e}"}, 400
    repository.update_transaction(id, amount, date, notes)
    return {"id": id, "amount": amount, "date": date, "notes": notes}


@app.route('/add_payment', methods=['GET'])
def add_payment_form():
    customers = repository.get_all_customers()
    default_month = session.get('last_statement_month', date.today().strftime('%Y-%m'))
    return render_template('upload_checks.html', customers=customers, statement_month=default_month)

@app.route('/add_payment', methods=['POST'])
def add_payment():
    # Cash payment — commit directly
    if 'cash_payment' in request.form:
        customer_id = request.form.get('customer_id_cash')
        amount = request.form.get('amount_cash')
        payment_date = date.today().strftime('%Y-%m-%d')
        notes = request.form.get('notes_cash', '')
        statement_month = request.form.get('statement_month_cash', '').strip() or None
        if statement_month:
            session['last_statement_month'] = statement_month
        transaction = repository.Transaction(
            id=None,
            customer_id=int(customer_id),
            transaction_type='Payment',
            amount=float(amount),
            date=payment_date,
            notes=notes if notes else 'Cash payment',
            statement_month=statement_month,
        )
        repository.add_transaction(transaction)
        return redirect(url_for('show_transactions'))

    # Manual check — send to review
    if 'manual_check' in request.form:
        customer_id = request.form.get('customer_id')
        check_number = request.form.get('check_id', '')
        amount = request.form.get('amount')
        payer_name = request.form.get('customer_search', '')
        statement_month = request.form.get('statement_month_manual', '').strip() or None
        if statement_month:
            session['last_statement_month'] = statement_month
            session['pending_statement_month'] = statement_month
        check = {
            'payer_name': payer_name,
            'customer_id': int(customer_id) if customer_id else None,
            'amount': float(amount) if amount else None,
            'check_number': check_number,
            'date': date.today().strftime('%Y-%m-%d'),
            'memo': None,
            'notes': f'Check #{check_number}' if check_number else '',
        }
        pending = session.get('pending_checks', [])
        pending.append(check)
        session['pending_checks'] = pending
        return redirect(url_for('review_checks'))

    # AI file upload
    files = request.files.getlist('checks')
    if not files or all(f.filename == '' for f in files):
        flash('No files selected.')
        return redirect(url_for('add_payment_form'))
    statement_month = request.form.get('statement_month_upload', '').strip() or None
    if statement_month:
        session['last_statement_month'] = statement_month
        session['pending_statement_month'] = statement_month
    customers = repository.get_all_customers()
    try:
        extracted = check_processor.extract_checks_from_files(files, customers)
    except Exception as e:
        flash(f'Error processing checks: {e}')
        return redirect(url_for('add_payment_form'))
    session['pending_checks'] = extracted
    return redirect(url_for('review_checks'))

@app.route('/review_checks')
def review_checks():
    pending = session.get('pending_checks', [])
    if not pending:
        return redirect(url_for('add_payment_form'))
    customers = repository.get_all_customers()
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template('review_checks.html', checks=pending, customers=customers, today=today)

@app.route('/commit_checks', methods=['POST'])
def commit_checks():
    statement_month = session.get('pending_statement_month')
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
                notes=request.form.get(f'notes_{index}', ''),
                statement_month=statement_month,
            )
            transactions.append(t)
        index += 1
    if transactions:
        repository.batch_insert_transactions(transactions)
    session.pop('pending_checks', None)
    session.pop('pending_statement_month', None)
    return redirect(url_for('show_transactions'))

@app.route('/add_charge', methods=['GET'])
def add_charge_form():
    customers = repository.get_all_customers()
    return render_template('add_charge.html', customers=customers,
                           current_month=date.today().strftime('%Y-%m'))

@app.route('/add_charge', methods=['POST'])
def add_charge():
    # Extra charge — single customer
    if 'extra_charge' in request.form:
        customer_id = request.form.get('customer_id_extra')
        amount = request.form.get('amount_extra')
        notes = request.form.get('notes_extra', '')
        charge_date = request.form.get('date_extra')
        transaction = repository.Transaction(
            id=None,
            customer_id=int(customer_id),
            transaction_type='Charge',
            amount=float(amount),
            date=charge_date,
            notes=notes
        )
        repository.add_transaction(transaction)
        return redirect(url_for('show_transactions'))

    # Monthly charges — bulk, respecting checkbox selections
    if 'monthly_charges' in request.form:
        month_monthly = request.form.get('month_monthly', date.today().strftime('%Y-%m'))
        charge_date = f"{month_monthly}-01"
        customers = repository.get_all_customers()
        for customer in customers:
            if request.form.get(f'customer_{customer.id}'):
                transaction = repository.Transaction(
                    id=None,
                    customer_id=customer.id,
                    transaction_type='Charge',
                    amount=customer.rate,
                    date=charge_date,
                    notes='Monthly charge'
                )
                repository.add_transaction(transaction)
        return redirect(url_for('show_transactions'))

@app.route('/monthly_charges/<int:year>/<int:month>')
def show_monthly_charge_statement(year: int, month: int):
    if month < 1 or month > 12:
        return {"error": "Invalid month"}, 400
    rows = repository.get_monthly_charge_statement(year, month)
    if not rows:
        flash(f"No monthly charges were run for {cal_module.month_name[month]} {year}.")
        return redirect(url_for('show_transactions'))
    total_charged   = sum(r["charge"].amount for r in rows)
    total_collected = sum(p.amount for r in rows for p in r["payments"])
    paid_count      = sum(1 for r in rows if r["payments"])
    prev_y, prev_m = (year, month - 1) if month > 1 else (year - 1, 12)
    next_y, next_m = (year, month + 1) if month < 12 else (year + 1, 1)
    return render_template(
        'monthly_charge_statement.html',
        rows=rows, year=year, month=month,
        month_name=cal_module.month_name[month],
        total_charged=total_charged,
        total_collected=total_collected,
        outstanding=total_charged - total_collected,
        paid_count=paid_count,
        total_count=len(rows),
        prev_year=prev_y, prev_month=prev_m,
        next_year=next_y, next_month=next_m,
    )


@app.route('/api/monthly_charge_exists')
def monthly_charge_exists():
    month_str = request.args.get('month', '')
    try:
        year, month = int(month_str[:4]), int(month_str[5:7])
    except (ValueError, IndexError):
        return {"error": "Invalid month format, expected YYYY-MM"}, 400
    count = repository.has_monthly_charges_for_month(year, month)
    return {"exists": count > 0, "count": count}


@app.route('/statements')
def show_statements():
    today = date.today()
    month_str = request.args.get('month', today.strftime('%Y-%m'))
    try:
        year, month = int(month_str[:4]), int(month_str[5:7])
    except (ValueError, IndexError):
        year, month = today.year, today.month
    customers = repository.get_all_customers()
    statements = []
    for customer in customers:
        data = repository.get_statement_data(customer.id, year, month)
        statements.append({"customer": customer, "data": data})
    month_name = cal_module.month_name[month]
    return render_template('statements.html', statements=statements,
                           month_str=month_str, year=year, month=month,
                           month_name=month_name)

@app.route('/customers/<int:id>/statement')
def show_customer_statement(id: int):
    customer = repository.get_specific_customer(id)
    if not customer:
        return {"error": f"No customer found with ID {id}"}, 404
    today = date.today()
    month_str = request.args.get('month', today.strftime('%Y-%m'))
    try:
        year, month = int(month_str[:4]), int(month_str[5:7])
    except (ValueError, IndexError):
        year, month = today.year, today.month
    data = repository.get_statement_data(id, year, month)
    month_name = cal_module.month_name[month]
    return render_template('customer_statement.html', customer=customer,
                           data=data, month_str=month_str,
                           month_name=month_name, year=year)