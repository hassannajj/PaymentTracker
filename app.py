from flask import Flask, request
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
    return 'Index Page'

@app.route("/hello")
def hello_world():
    name = request.args.get("name", "Flask")

    return f"<p>Hello, {escape(name)}!</p>"

@app.route('/customers')
def show_customers():
    customers = repository.get_all_customers()
    return '<br>'.join([f'Customer {c.id}: {c.name} {c.rate}' for c in customers])

@app.route('/customer/<int:id>')
def show_customer_profile(id: int):
    customer = repository.get_specific_customer(id)
    if not customer:
        return {"error": f"No customer found with ID {id}"}, 404
    transactions = repository.get_transactions_for_customer(id)

    display = f'Customer {customer.id}: {customer.name} {customer.rate}<br><br>'
    if transactions:
        display += 'Transactions:<br>'
        display += '<br>'.join([f'{t.transaction_type} {t.amount} on {t.date} ({t.notes})' for t in transactions])
    else:
        display += 'No transactions found for this customer.'
    return display

@app.route('/transactions')
def show_transactions():
    transactions = repository.get_all_transactions()
    return '<br>'.join([f'Transaction for Customer {t.customer_id}: {t.transaction_type} {t.amount} on {t.date} ({t.notes})' for t in transactions])