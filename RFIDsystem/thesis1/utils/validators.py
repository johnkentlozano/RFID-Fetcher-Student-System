import re

def is_strong_password(password: str) -> bool:
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[\W_]).{8,}$'
    return re.match(pattern, password) is not None

def validate_required(*fields):
    return all(field.strip() != "" for field in fields)