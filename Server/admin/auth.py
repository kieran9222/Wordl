"""Server — password hashing and session-token helpers, moved from Client/wordl.py
since the server is now the sole owner of credential verification."""
import hashlib
import secrets


def hash_password(password: str) -> str:
    '''hashes password, generates salt'''
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000).hex()
    return f"sha256:{salt}:{h}"


def verify_password(password: str, stored: str) -> bool:
    '''checks a password guess against the stored hash'''
    _, salt, expected = stored.split(":")
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000).hex()
    return secrets.compare_digest(h, expected)


def generate_token() -> str:
    '''generates a random opaque session token'''
    return secrets.token_hex(32)
