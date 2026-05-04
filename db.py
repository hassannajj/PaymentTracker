from flask import g, session, has_request_context
import sqlite3
import os

DEFAULT_DB = os.environ.get('DATABASE_PATH', 'data/data.db')

def get_db_path():
    if has_request_context():
        return session.get('db_path', DEFAULT_DB)
    return DEFAULT_DB

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
