import sqlite3

from flask import Flask, jsonify, request, send_from_directory

from validation import validate_profile


def create_app(db_path=":memory:"):
    app = Flask(__name__)
    db = sqlite3.connect(db_path, check_same_thread=False)
    db.execute("CREATE TABLE IF NOT EXISTS profiles (email TEXT UNIQUE NOT NULL, birth_date TEXT NOT NULL)")

    @app.get("/")
    def index():
        return send_from_directory(".", "index.html")

    @app.post("/profile")
    def save():
        data = request.get_json(silent=True) or {}
        clean, errors = validate_profile(data)
        if errors:
            return jsonify({"errors": errors}), 422
        try:
            db.execute("INSERT INTO profiles VALUES (?, ?)", (clean["email"], clean["birth_date"]))
            db.commit()
        except sqlite3.IntegrityError:
            return jsonify({"errors": {"email": "Этот email уже используется"}}), 409
        return jsonify(clean), 201

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
