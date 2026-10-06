import unittest
from datetime import date

from app import create_app
from validation import validate_profile

TODAY = date(2026, 10, 6)


class ValidationTest(unittest.TestCase):
    def check(self, data):
        return validate_profile(data, today=TODAY)

    def test_valid(self):
        clean, errors = self.check({"email": "  Ann@Example.COM ", "birth_date": "2000-02-29"})
        self.assertEqual(errors, {})
        self.assertEqual(clean, {"email": "ann@example.com", "birth_date": "2000-02-29"})

    def test_bad_emails(self):
        for e in ["", "abc", "a@b", "a b@c.com", "@c.com", None, 5]:
            with self.subTest(email=e):
                self.assertIn("email", self.check({"email": e, "birth_date": "2000-01-01"})[1])

    def test_bad_dates(self):
        for d in ["", "01.01.2000", "2001-02-29", "2026-10-07", "1800-01-01", None]:
            with self.subTest(date=d):
                self.assertIn("birth_date", self.check({"email": "a@b.co", "birth_date": d})[1])

    def test_today_is_allowed(self):
        self.assertEqual(self.check({"email": "a@b.co", "birth_date": "2026-10-06"})[1], {})


class EndpointTest(unittest.TestCase):
    def test_errors_per_field_and_duplicate(self):
        c = create_app().test_client()
        r = c.post("/profile", json={"email": "bad", "birth_date": "2999-01-01"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(set(r.json["errors"]), {"email", "birth_date"})
        ok = {"email": "a@b.co", "birth_date": "2000-01-01"}
        self.assertEqual(c.post("/profile", json=ok).status_code, 201)
        self.assertEqual(c.post("/profile", json=ok).status_code, 409)


if __name__ == "__main__":
    unittest.main()
