import unittest

from auth_lib import AuthError, issue_token, require_role, verify_token
from clients import MobileClient, WebClient

NOW = 1_700_000_000
GOLDEN = ("eyJleHAiOjE3MDAwMDA5MDAsImlhdCI6MTcwMDAwMDAwMCwicm9sZSI6Im1hbmFnZXIiLCJzdWIiOiJ1MSJ9."
          "rksLeTZ9hRJ8TLOYFEGbFd46u-wWIpIdKZxOL1gszaA")


class LibraryUnitTests(unittest.TestCase):
    def test_roundtrip(self):
        p = verify_token(issue_token("u1", "admin", now=NOW), now=NOW + 1)
        self.assertEqual((p["sub"], p["role"]), ("u1", "admin"))

    def test_expiry_boundary(self):
        t = issue_token("u1", ttl=900, now=NOW)
        verify_token(t, now=NOW + 899)
        for moment in (NOW + 900, NOW + 901):
            with self.subTest(now=moment), self.assertRaises(AuthError):
                verify_token(t, now=moment)

    def test_tampering_detected(self):
        body, sig = issue_token("u1", "user", now=NOW).split(".")
        forged = issue_token("u1", "admin", now=NOW).split(".")[0] + "." + sig
        for bad in (forged, body + "." + sig[:-2] + "xx", body, "", "a.b.c", None):
            with self.subTest(token=bad), self.assertRaises(AuthError):
                verify_token(bad, now=NOW)

    def test_wrong_secret_rejected(self):
        with self.assertRaises(AuthError):
            verify_token(issue_token("u1", now=NOW, secret=b"other"), now=NOW)

    def test_role_hierarchy(self):
        admin = verify_token(issue_token("a", "admin", now=NOW), now=NOW)
        user = verify_token(issue_token("u", "user", now=NOW), now=NOW)
        require_role(admin, "manager")
        with self.assertRaises(AuthError):
            require_role(user, "manager")


class BackwardCompatibilityRegression(unittest.TestCase):
    def test_old_token_still_valid(self):
        self.assertEqual(verify_token(GOLDEN, now=NOW + 10)["role"], "manager")

    def test_token_format_is_unchanged(self):
        self.assertEqual(issue_token("u1", "manager", ttl=900, now=NOW), GOLDEN)


class ContractTests(unittest.TestCase):
    def test_both_clients_same_behaviour(self):
        for make in (WebClient, MobileClient):
            with self.subTest(client=make.__name__):
                c = make()
                c.login("u7", now=NOW)
                self.assertEqual(c.current_user(now=NOW + 10), "u7")
                with self.assertRaises(AuthError):
                    c.current_user(now=NOW + 10_000)
                with self.assertRaises(AuthError):
                    make().current_user(now=NOW)

    def test_mobile_refreshes_token_near_expiry(self):
        m = MobileClient()
        m.login("u7", now=NOW)
        old = m.keychain["token"]
        m.current_user(now=NOW + 850)
        self.assertNotEqual(m.keychain["token"], old)
        self.assertEqual(verify_token(m.keychain["token"], now=NOW + 851)["sub"], "u7")


if __name__ == "__main__":
    unittest.main()
