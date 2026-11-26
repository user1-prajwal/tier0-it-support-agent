from sqlalchemy import text

PASSWORD = "password-for-tests"  # the password the auth_client fixture seeds


def login(client, email, password=PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_works_and_every_failure_looks_the_same(auth_client):
    ok = login(auth_client, "alice@demo.local")
    assert ok.status_code == 200
    me = auth_client.get("/auth/me", headers=bearer(ok.json()["access_token"]))
    assert me.json() == {
        "email": "alice@demo.local",
        "display_name": "Alice",
        "role": "employee",
        "groups": ["everyone"],
    }

    failures = [
        login(auth_client, "alice@demo.local", "wrong password"),
        login(auth_client, "nobody@demo.local"),
        login(auth_client, "erin@demo.local"),  # right password, deactivated account
    ]
    assert {r.status_code for r in failures} == {401}
    assert len({r.text for r in failures}) == 1  # identical bodies: nothing says which case it was
    assert auth_client.get("/auth/me").status_code == 401  # no token


def test_group_and_account_changes_apply_on_the_next_request_with_the_same_token(
    auth_client, engine
):
    headers = bearer(login(auth_client, "bob@demo.local").json()["access_token"])
    assert set(auth_client.get("/auth/me", headers=headers).json()["groups"]) == {
        "everyone",
        "helpdesk",
    }

    with engine.begin() as conn:  # revoke a group
        conn.execute(
            text(
                "DELETE FROM user_groups WHERE"
                " user_id = (SELECT id FROM users WHERE email = 'bob@demo.local')"
                " AND group_id = (SELECT id FROM groups WHERE name = 'helpdesk')"
            )
        )
    assert auth_client.get("/auth/me", headers=headers).json()["groups"] == ["everyone"]

    with engine.begin() as conn:  # deactivate the account
        conn.execute(text("UPDATE users SET is_active = false WHERE email = 'bob@demo.local'"))
    assert auth_client.get("/auth/me", headers=headers).status_code == 401


def test_repeated_failures_block_even_the_right_password(auth_client):
    for _ in range(5):
        assert login(auth_client, "alice@demo.local", "wrong").status_code == 401

    blocked = login(auth_client, "alice@demo.local")  # the correct password
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers