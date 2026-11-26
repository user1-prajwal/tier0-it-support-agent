from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()  # argon2id with the library's current default cost settings


def hash_password(password: str) -> str:
    """The stored form: algorithm, cost settings, random salt and hash in one string."""
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """True only for the right password. A wrong password or a malformed hash is just False."""
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False