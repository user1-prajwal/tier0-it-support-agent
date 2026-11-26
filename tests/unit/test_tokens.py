import base64
import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.auth.tokens import InvalidToken, create_access_token, decode_access_token

SECRET = "a-test-secret-that-is-at-least-32-characters-long"


def b64(data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()


def test_a_valid_token_returns_the_user_id():
    assert decode_access_token(create_access_token(42, SECRET), SECRET) == 42


def test_forged_expired_and_malformed_tokens_are_rejected():
    good = create_access_token(42, SECRET)
    header, _, signature = good.split(".")
    expiring = {"sub": "42", "exp": datetime.now(UTC) + timedelta(minutes=5)}

    bad_tokens = {
        # The realistic attack: change who the token says you are, keep the old signature.
        "changed payload": f"{header}.{b64({'sub': '1', 'exp': 9999999999})}.{signature}",
        "signed with another secret": jwt.encode(
            expiring, "another-secret-that-is-also-32-characters-long", algorithm="HS256"
        ),
        "alg none": jwt.encode(expiring, None, algorithm="none"),
        "expired": create_access_token(
            42, SECRET, minutes=60, now=datetime.now(UTC) - timedelta(hours=2)
        ),
        "no expiry": jwt.encode({"sub": "42"}, SECRET, algorithm="HS256"),
        "garbage": "not.a.token",
        "empty": "",
    }
    for name, token in bad_tokens.items():
        with pytest.raises(InvalidToken):
            decode_access_token(token, SECRET)
        assert name  # shows which case failed if one is ever accepted


def test_an_empty_or_short_secret_is_refused():
    for bad in ["", "short"]:
        with pytest.raises(ValueError):
            create_access_token(1, bad)
        with pytest.raises(ValueError):
            decode_access_token("x.y.z", bad)