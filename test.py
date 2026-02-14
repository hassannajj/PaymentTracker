import sqlite3

con = sqlite3.connect("demo-data2.db")
cur = con.cursor()



def create_customers_table():
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            rate INTEGER
        )
        """)
    con.commit()

def drop_customers_table():
    cur.execute("DROP TABLE IF EXISTS customers")
    con.commit()

def populate_customers_table():
    data = [
        (0, 'Rick', 150),
        (1, 'Samantha', 200),
        (2, 'Greg', 175)
    ]
    cur.executemany(
        "INSERT INTO customers VALUES (?, ?, ?)",
        data
    )
    con.commit()

# TODO: Update customer rate by id


def read_customers_table(): # Returns list of tuples (id, name, rate)
    cur.execute("SELECT id, name, rate FROM customers")
    return cur.fetchall()


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

def drop_transactions_table():
    cur.execute("DROP TABLE IF EXISTS transactions")
    con.commit()

def populate_transactions_table():
    data = [
        (0, 'Charge', 300, '2024-01-01', 'Project A'),
        (0, 'Payment', 150, '2024-01-15', 'Partial payment for Project A'),
        (1, 'Charge', 400, '2024-02-01', 'Project B'),
        (2, 'Charge', 350, '2024-03-01', 'Project C'),
        (2, 'Payment', 175, '2024-03-15', 'Partial payment for Project C')
    ]
    cur.executemany(
        "INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
        data
    )
    con.commit()

# TODO: Update transaction 

def read_transactions_table(): # Returns list of tuples (customer_id, transaction_type, amount, date, notes)
    cur.execute("SELECT customer_id, transaction_type, amount, date, notes FROM transactions")
    return cur.fetchall()



drop_customers_table()
create_customers_table()
populate_customers_table()
customer_data = read_customers_table()
for id, name, rate in customer_data:
    print(f"ID: {id}, Name: {name}, Rate: {rate}")

drop_transactions_table()
create_transactions_table()
populate_transactions_table ()
transaction_data = read_transactions_table()
for customer_id, transaction_type, amount, date, notes in transaction_data:
    print(f"Customer ID: {customer_id}, Transaction Type: {transaction_type}, Amount: {amount}, Date: {date}, Notes: {notes}")

con.close()