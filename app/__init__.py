from typing import Literal, overload
import sqlite3
import os

from flask import Flask, g

app = Flask(__name__)

DB_PATH = "save.db"
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_db() -> sqlite3.Connection:
    """Get a database connection."""
    if "_database" not in g:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        g._database = db
    return g._database


@overload
def query_db(
    query: str, args: tuple | None = (), *, single: Literal[True]
) -> sqlite3.Row | None: ...


@overload
def query_db(
    query: str, args: tuple | None = (), single: Literal[False] = False
) -> list[sqlite3.Row]: ...


def query_db(query: str, args: tuple | None = (), single: bool = False):
    """Query the database."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if single else rv


@app.teardown_appcontext
def close_connection(_):
    db: sqlite3.Connection | None = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.cli.command("init-db")
def init_db():
    """Apply the database schema."""
    with app.app_context(), open(SCHEMA_PATH, "r") as f:
        get_db().executescript(f.read())
        get_db().commit()


@app.route("/")
def hello():
    return "Hello!"
