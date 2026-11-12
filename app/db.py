"""Camada de acesso a dados (SQLite). Todas as consultas são parametrizadas."""
import os
import sqlite3

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE"]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema, encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


# ---------- usuários ----------
def get_user_by_username(username):
    return get_db().execute(
        "SELECT * FROM user WHERE username = ?", (username,)
    ).fetchone()


def get_user(user_id):
    return get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()


def insert_user(username, password_hash):
    db = get_db()
    db.execute(
        "INSERT INTO user (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    db.commit()


# ---------- produtos ----------
def list_products(only_active=False, search=None):
    sql = "SELECT * FROM product"
    clauses, params = [], []
    if only_active:
        clauses.append("active = 1")
    if search:
        clauses.append("name LIKE ?")
        params.append(f"%{search}%")
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY name COLLATE NOCASE"
    return get_db().execute(sql, params).fetchall()


def get_product(product_id):
    return get_db().execute(
        "SELECT * FROM product WHERE id = ?", (product_id,)
    ).fetchone()


def insert_product(name, price_cents, stock, active):
    db = get_db()
    cur = db.execute(
        "INSERT INTO product (name, price_cents, stock, active) VALUES (?, ?, ?, ?)",
        (name, price_cents, stock, 1 if active else 0),
    )
    db.commit()
    return cur.lastrowid


def update_product(product_id, name, price_cents, stock, active):
    db = get_db()
    db.execute(
        "UPDATE product SET name = ?, price_cents = ?, stock = ?, active = ? WHERE id = ?",
        (name, price_cents, stock, 1 if active else 0, product_id),
    )
    db.commit()


# ---------- vendas ----------
def insert_sale(items, total_cents, deduct_stock):
    """Grava a venda e seus itens em uma única transação.

    items: lista de dicts com product_id, quantity, unit_price_cents, subtotal_cents.
    Se deduct_stock for True, a baixa só acontece se houver estoque suficiente
    (a condição está no próprio UPDATE, então não há corrida entre vendas).
    Retorna o id da venda, ou levanta ValueError com o id do produto sem estoque.
    """
    db = get_db()
    try:
        cur = db.execute("INSERT INTO sale (total_cents) VALUES (?)", (total_cents,))
        sale_id = cur.lastrowid
        for it in items:
            db.execute(
                "INSERT INTO sale_item (sale_id, product_id, quantity, unit_price_cents, subtotal_cents)"
                " VALUES (?, ?, ?, ?, ?)",
                (sale_id, it["product_id"], it["quantity"],
                 it["unit_price_cents"], it["subtotal_cents"]),
            )
            if deduct_stock:
                res = db.execute(
                    "UPDATE product SET stock = stock - ? WHERE id = ? AND stock >= ?",
                    (it["quantity"], it["product_id"], it["quantity"]),
                )
                if res.rowcount == 0:
                    raise ValueError(it["product_id"])
        db.commit()
        return sale_id
    except Exception:
        db.rollback()
        raise


def list_sales(limit=100):
    return get_db().execute(
        "SELECT s.id, s.created_at, s.total_cents,"
        " (SELECT COALESCE(SUM(quantity), 0) FROM sale_item WHERE sale_id = s.id) AS items_count"
        " FROM sale s ORDER BY s.id DESC LIMIT ?",
        (limit,),
    ).fetchall()


def sales_summary():
    return get_db().execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(total_cents), 0) AS total FROM sale"
    ).fetchone()


@click.command("init-db")
def init_db_command():
    """Cria as tabelas do banco de dados."""
    init_db()
    click.echo("Banco de dados inicializado.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
