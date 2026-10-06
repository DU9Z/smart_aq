import unittest

from registration import create_app, hash_password, validate_registration

VALID = {"name": "Аня", "email": "ann@example.com", "password": "secret123"}


class UnitTests(unittest.TestCase):
    def test_valid_data_has_no_errors(self):
        self.assertEqual(validate_registration(VALID), {})

    def test_required_fields(self):
        self.assertEqual(set(validate_registration({})), {"name", "email", "password"})
        self.assertIn("name", validate_registration({**VALID, "name": "   "}))

    def test_email_formats(self):
        for bad in ["abc", "a@b", "a@", "@b.com", "a b@c.com"]:
            with self.subTest(email=bad):
                self.assertIn("email", validate_registration({**VALID, "email": bad}))

    def test_password_length_boundary(self):
        self.assertIn("password", validate_registration({**VALID, "password": "1234567"}))
        self.assertNotIn("password", validate_registration({**VALID, "password": "12345678"}))

    def test_hash_is_salted(self):
        self.assertNotEqual(hash_password("x" * 8), hash_password("x" * 8))


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.c = self.app.test_client()

    def test_success_creates_user_with_hashed_password(self):
        r = self.c.post("/register", json=VALID)
        self.assertEqual(r.status_code, 201)
        row = self.app.db.execute("SELECT email, password_hash FROM users").fetchone()
        self.assertEqual(row[0], "ann@example.com")
        self.assertNotIn("secret123", row[1])

    def test_duplicate_email_is_409_even_with_different_case(self):
        self.c.post("/register", json=VALID)
        r = self.c.post("/register", json={**VALID, "email": "ANN@example.com"})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json["errors"]["email"], "Этот email уже занят")
        self.assertEqual(self.app.db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 1)

    def test_invalid_data_does_not_touch_db(self):
        r = self.c.post("/register", json={**VALID, "email": "oops"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.app.db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
