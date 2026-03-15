import bcrypt  
import re

def hash_password(password: str) -> str:
    """Hash password using bcrypt with a high work factor."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()

def check_password(password: str, hashed: str) -> bool:
    """Verify a plain password against a stored hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def is_strong_password(password):
    return re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[\W_]).{8,}$', password)

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain password against the hashed version"""
    return bcrypt.checkpw(password.encode(), hashed.encode())