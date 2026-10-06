import base64
import itertools

from flask import Flask, jsonify, request

STATUSES = {"todo", "in_progress", "done"}
MAX_LIMIT = 100


def error(status, code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def encode_cursor(last_id):
    return base64.urlsafe_b64encode(str(last_id).encode()).decode()


def decode_cursor(cursor):
    return int(base64.urlsafe_b64decode(cursor.encode()).decode())


def create_app():
    app = Flask(__name__)
    tasks = {}
    ids = itertools.count(1)

    @app.post("/tasks")
    def create_task():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return error(400, "invalid_json", "Тело запроса должно быть JSON-объектом")
        title = data.get("title")
        if not isinstance(title, str) or not (1 <= len(title.strip()) <= 200):
            return error(422, "validation_error", "Некорректные данные",
                         {"title": "обязательная строка 1-200 символов"})
        task_id = next(ids)
        tasks[task_id] = {"id": task_id, "title": title.strip(), "status": "todo"}
        resp = jsonify(tasks[task_id])
        resp.status_code = 201
        resp.headers["Location"] = f"/tasks/{task_id}"
        return resp

    @app.get("/tasks")
    def list_tasks():
        try:
            limit = int(request.args.get("limit", 20))
            after = decode_cursor(request.args["cursor"]) if "cursor" in request.args else 0
        except (ValueError, UnicodeDecodeError):
            return error(400, "invalid_param", "limit или cursor имеют неверный формат")
        if not 1 <= limit <= MAX_LIMIT:
            return error(422, "validation_error", f"limit должен быть от 1 до {MAX_LIMIT}")
        status = request.args.get("status")
        if status and status not in STATUSES:
            return error(422, "validation_error", "Неизвестный статус", {"status": sorted(STATUSES)})
        rows = [t for t in sorted(tasks.values(), key=lambda t: t["id"])
                if t["id"] > after and (not status or t["status"] == status)]
        page = rows[:limit]
        has_more = len(rows) > limit
        return jsonify({"items": page,
                        "next_cursor": encode_cursor(page[-1]["id"]) if has_more else None})

    @app.get("/tasks/<int:task_id>")
    def get_task(task_id):
        task = tasks.get(task_id)
        return jsonify(task) if task else error(404, "not_found", "Задача не найдена")

    @app.patch("/tasks/<int:task_id>")
    def update_status(task_id):
        task = tasks.get(task_id)
        if not task:
            return error(404, "not_found", "Задача не найдена")
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or data.get("status") not in STATUSES:
            return error(422, "validation_error", "Некорректный статус", {"status": sorted(STATUSES)})
        task["status"] = data["status"]
        return jsonify(task)

    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        if tasks.pop(task_id, None) is None:
            return error(404, "not_found", "Задача не найдена")
        return "", 204

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
