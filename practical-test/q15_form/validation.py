import re
from datetime import date, datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
MAX_AGE = 120


def validate_profile(data, today=None):
    today = today or date.today()
    errors, clean = {}, {}

    email = data.get("email")
    if not isinstance(email, str) or not email.strip():
        errors["email"] = "Укажите email"
    else:
        email = email.strip().lower()
        if len(email) > 254 or not EMAIL_RE.match(email):
            errors["email"] = "Введите email в формате name@example.com"
        else:
            clean["email"] = email

    raw = data.get("birth_date")
    if not isinstance(raw, str) or not raw:
        errors["birth_date"] = "Укажите дату рождения"
    else:
        try:
            born = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            errors["birth_date"] = "Дата должна быть в формате ГГГГ-ММ-ДД и существовать в календаре"
        else:
            if born > today:
                errors["birth_date"] = "Дата рождения не может быть в будущем"
            elif today.year - born.year > MAX_AGE:
                errors["birth_date"] = f"Возраст не может быть больше {MAX_AGE} лет"
            else:
                clean["birth_date"] = born.isoformat()
    return clean, errors
