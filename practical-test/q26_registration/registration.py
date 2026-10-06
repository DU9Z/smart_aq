import hashlib
import os
import re
import sqlite3

from flask import Flask, jsonify, request

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


def validate_registration(data):
    errors = {}
    for field in ("name", "email", "password"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors[field] = "Обязательное поле"
    if "email" not in errors and not EMAIL_RE.match(data["email"].strip()):
        errors["email"] = "Некорректный email"
    if "password" not in errors and len(data["password"]) < 8:
        errors["password"] = "Минимум 8 символов"
    return errors


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    return salt.hex() + ":" + hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1).hex()


def create_app():
    app = Flask(__name__)
    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password_hash TEXT)")
    app.db = db

    @app.post("/register")
    def register():
        data = request.get_json(silent=True) or {}
        errors = validate_registration(data)
        if errors:
            return jsonify({"errors": errors}), 422
        email = data["email"].strip().lower()
        try:
            cur = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                             (data["name"].strip(), email, hash_password(data["password"])))
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"errors": {"email": "Этот email уже занят"}}), 409
        return jsonify({"id": cur.lastrowid, "email": email}), 201

    return app
