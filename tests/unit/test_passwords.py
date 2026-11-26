from app.auth.passwords import hash_password, verify_password


def test_a_password_verifies_and_a_wrong_one_does_not():
    stored = hash_password("correct horse")
    assert "correct horse" not in stored
    assert verify_password(stored, "correct horse") is True
    assert verify_password(stored, "wrong password") is False


def test_a_malformed_stored_hash_is_a_failed_login_not_a_crash():
    assert verify_password("not-a-hash", "anything") is False
    assert verify_password("", "anything") is False