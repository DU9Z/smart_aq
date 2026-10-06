from auth_lib import AuthError, issue_token, verify_token

REFRESH_BEFORE = 60


class WebClient:
    def __init__(self):
        self.cookie = {}

    def login(self, user_id, role="user", now=None):
        self.cookie["token"] = issue_token(user_id, role, now=now)

    def current_user(self, now=None):
        return verify_token(self.cookie.get("token", ""), now=now)["sub"]


class MobileClient:
    def __init__(self):
        self.keychain = {}

    def login(self, user_id, role="user", now=None):
        self.keychain["token"] = issue_token(user_id, role, now=now)

    def current_user(self, now=None):
        payload = verify_token(self.keychain.get("token", ""), now=now)
        if payload["exp"] - (now if now is not None else payload["iat"]) < REFRESH_BEFORE:
            self.keychain["token"] = issue_token(payload["sub"], payload["role"], now=now)
        return payload["sub"]
