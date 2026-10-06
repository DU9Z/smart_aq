import sqlite3

from flask import Flask, jsonify, request

TOKEN = "Bearer test-token"


def error(status, code, message, **extra):
    return jsonify({"error": {"code": code, "message": message, **extra}}), status


def create_app(db_path, fail_after_stock_update=False):
    app = Flask(__name__)

    def connect():
        con = sqlite3.connect(db_path, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        return con

    with connect() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, stock INTEGER NOT NULL CHECK (stock >= 0));
            CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, product_id INTEGER, qty INTEGER, idem_key TEXT UNIQUE);
        """)

    @app.post("/orders")
    def create_order():
        if request.headers.get("Authorization") != TOKEN:
            return error(401, "unauthorized", "Требуется авторизация")
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return error(400, "invalid_json", "Тело должно быть JSON-объектом")
        pid, qty = data.get("product_id"), data.get("qty")
        is_int = lambda v: isinstance(v, int) and not isinstance(v, bool)
        if not is_int(pid) or not is_int(qty) or not 1 <= qty <= 100:
            return error(422, "validation_error", "product_id — целое, qty — целое от 1 до 100")
        key = request.headers.get("Idempotency-Key")

        con = connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            if key:
                row = con.execute("SELECT id FROM orders WHERE idem_key = ?", (key,)).fetchone()
                if row:
                    con.execute("COMMIT")
                    return jsonify({"order_number": row["id"], "replayed": True}), 200
            cur = con.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (qty, pid, qty))
            if cur.rowcount == 0:
                row = con.execute("SELECT stock FROM products WHERE id = ?", (pid,)).fetchone()
                con.execute("ROLLBACK")
                if row is None:
                    return error(404, "product_not_found", "Товар не найден")
                return error(409, "insufficient_stock", "Недостаточно товара", available=row["stock"])
            if fail_after_stock_update:
                raise RuntimeError("симуляция сбоя между списанием и записью заказа")
            cur = con.execute("INSERT INTO orders (product_id, qty, idem_key) VALUES (?, ?, ?)", (pid, qty, key))
            con.execute("COMMIT")
            return jsonify({"order_number": cur.lastrowid}), 201
        except Exception:
            if con.in_transaction:
                con.execute("ROLLBACK")
            raise
        finally:
            con.close()

    return app
