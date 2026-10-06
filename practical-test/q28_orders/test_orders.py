import os
import sqlite3
import tempfile
import threading
import unittest

from orders import TOKEN, create_app

AUTH = {"Authorization": TOKEN}


class OrdersIntegrationTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.app = create_app(self.path)
        con = sqlite3.connect(self.path)
        con.execute("INSERT INTO products VALUES (1, 3)")
        con.commit()
        con.close()
        self.c = self.app.test_client()

    def tearDown(self):
        os.remove(self.path)

    def db(self, sql):
        con = sqlite3.connect(self.path)
        try:
            return con.execute(sql).fetchall()
        finally:
            con.close()

    def test_success_returns_201_number_and_decrements_stock(self):
        r = self.c.post("/orders", json={"product_id": 1, "qty": 2}, headers=AUTH)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["order_number"], 1)
        self.assertEqual(self.db("SELECT stock FROM products WHERE id=1"), [(1,)])
        self.assertEqual(self.db("SELECT product_id, qty FROM orders"), [(1, 2)])

    def test_order_for_exact_remaining_stock(self):
        self.assertEqual(self.c.post("/orders", json={"product_id": 1, "qty": 3}, headers=AUTH).status_code, 201)
        self.assertEqual(self.db("SELECT stock FROM products"), [(0,)])

    def test_idempotent_retry_creates_one_order(self):
        h = {**AUTH, "Idempotency-Key": "abc-1"}
        first = self.c.post("/orders", json={"product_id": 1, "qty": 1}, headers=h)
        second = self.c.post("/orders", json={"product_id": 1, "qty": 1}, headers=h)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json["order_number"], second.json["order_number"])
        self.assertEqual(self.db("SELECT stock FROM products"), [(2,)])
        self.assertEqual(self.db("SELECT COUNT(*) FROM orders"), [(1,)])

    def test_not_enough_stock_409_and_nothing_changes(self):
        r = self.c.post("/orders", json={"product_id": 1, "qty": 4}, headers=AUTH)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json["error"]["available"], 3)
        self.assertEqual(self.db("SELECT stock FROM products"), [(3,)])
        self.assertEqual(self.db("SELECT COUNT(*) FROM orders"), [(0,)])

    def test_unknown_product_404(self):
        self.assertEqual(self.c.post("/orders", json={"product_id": 99, "qty": 1}, headers=AUTH).status_code, 404)

    def test_validation_422(self):
        for body in [{}, {"product_id": 1}, {"product_id": 1, "qty": 0}, {"product_id": 1, "qty": -1},
                     {"product_id": 1, "qty": "2"}, {"product_id": 1, "qty": True}, {"product_id": 1, "qty": 101}]:
            with self.subTest(body=body):
                self.assertEqual(self.c.post("/orders", json=body, headers=AUTH).status_code, 422)

    def test_no_auth_401_and_bad_json_400(self):
        self.assertEqual(self.c.post("/orders", json={"product_id": 1, "qty": 1}).status_code, 401)
        self.assertEqual(self.c.post("/orders", data="xx", headers=AUTH).status_code, 400)

    def test_failure_between_steps_rolls_back_stock(self):
        app = create_app(self.path, fail_after_stock_update=True)
        r = app.test_client().post("/orders", json={"product_id": 1, "qty": 2}, headers=AUTH)
        self.assertEqual(r.status_code, 500)
        self.assertEqual(self.db("SELECT stock FROM products"), [(3,)])
        self.assertEqual(self.db("SELECT COUNT(*) FROM orders"), [(0,)])

    def test_concurrent_orders_never_oversell(self):
        codes = []

        def buy():
            r = self.app.test_client().post("/orders", json={"product_id": 1, "qty": 1}, headers=AUTH)
            codes.append(r.status_code)

        threads = [threading.Thread(target=buy) for _ in range(8)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sorted(codes), [201] * 3 + [409] * 5)
        self.assertEqual(self.db("SELECT stock FROM products"), [(0,)])
        self.assertEqual(self.db("SELECT COUNT(*) FROM orders"), [(3,)])


if __name__ == "__main__":
    unittest.main()
