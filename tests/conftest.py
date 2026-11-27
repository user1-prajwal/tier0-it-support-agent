import pytest
from argon2 import PasswordHasher

from app.auth import passwords


@pytest.fixture(autouse=True, scope="session")
def cheap_password_hashing():
    """TESTS ONLY: minimal argon2 cost, so seeding users stays fast.

    The production hasher is untouched. verify() reads the cost settings stored in each hash.
    """
    original = passwords._hasher
    passwords._hasher = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    yield
    passwords._hasher = original