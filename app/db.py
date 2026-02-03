import sqlite3
from datetime import datetime
from typing import Literal, overload

import click
from flask import Flask, current_app, g
from werkzeug.security import generate_password_hash


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


@overload
def query_db(
    query: str, args: tuple | None = (), *, single: Literal[True]
) -> sqlite3.Row | None: ...


@overload
def query_db(
    query: str, args: tuple | None = (), single: Literal[False] = False
) -> list[sqlite3.Row]: ...


def query_db(query: str, args: tuple | None = (), single: bool = False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if single else rv


def close_db(_):
    db: sqlite3.Connection | None = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))

        password_hash = generate_password_hash("password")
        db.execute(
            "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
            ("default admin", password_hash, 1),
        )
        db.commit()


@click.command("init-db")
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


sqlite3.register_converter("timestamp", lambda v: datetime.fromisoformat(v.decode()))


def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
