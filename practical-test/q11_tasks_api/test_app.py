import unittest

from app import create_app


class TasksApiTest(unittest.TestCase):
    def setUp(self):
        self.c = create_app().test_client()

    def make(self, n):
        for i in range(n):
            self.c.post("/tasks", json={"title": f"t{i}"})

    def test_create_returns_201_and_location(self):
        r = self.c.post("/tasks", json={"title": "Купить молоко"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json, {"id": 1, "title": "Купить молоко", "status": "todo"})
        self.assertEqual(r.headers["Location"], "/tasks/1")

    def test_create_validation(self):
        self.assertEqual(self.c.post("/tasks", json={"title": "  "}).status_code, 422)
        self.assertEqual(self.c.post("/tasks", json={"title": "x" * 201}).status_code, 422)
        self.assertEqual(self.c.post("/tasks", data="не json").status_code, 400)

    def test_get_and_404(self):
        self.make(1)
        self.assertEqual(self.c.get("/tasks/1").status_code, 200)
        r = self.c.get("/tasks/99")
        self.assertEqual((r.status_code, r.json["error"]["code"]), (404, "not_found"))

    def test_patch_status(self):
        self.make(1)
        self.assertEqual(self.c.patch("/tasks/1", json={"status": "done"}).json["status"], "done")
        self.assertEqual(self.c.patch("/tasks/1", json={"status": "???"}).status_code, 422)
        self.assertEqual(self.c.patch("/tasks/9", json={"status": "done"}).status_code, 404)

    def test_delete(self):
        self.make(1)
        self.assertEqual(self.c.delete("/tasks/1").status_code, 204)
        self.assertEqual(self.c.delete("/tasks/1").status_code, 404)

    def test_cursor_pagination_walks_all_items_without_duplicates(self):
        self.make(5)
        seen, cursor = [], None
        while True:
            url = "/tasks?limit=2" + (f"&cursor={cursor}" if cursor else "")
            body = self.c.get(url).json
            seen += [t["id"] for t in body["items"]]
            cursor = body["next_cursor"]
            if not cursor:
                break
        self.assertEqual(seen, [1, 2, 3, 4, 5])

    def test_pagination_stable_after_delete(self):
        self.make(4)
        first = self.c.get("/tasks?limit=2").json
        self.c.delete("/tasks/1")
        second = self.c.get(f"/tasks?limit=2&cursor={first['next_cursor']}").json
        self.assertEqual([t["id"] for t in second["items"]], [3, 4])

    def test_bad_params(self):
        self.assertEqual(self.c.get("/tasks?limit=0").status_code, 422)
        self.assertEqual(self.c.get("/tasks?limit=abc").status_code, 400)
        self.assertEqual(self.c.get("/tasks?cursor=%%%").status_code, 400)


if __name__ == "__main__":
    unittest.main()
