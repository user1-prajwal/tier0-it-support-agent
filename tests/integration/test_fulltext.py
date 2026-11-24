from sqlalchemy import text

from app.db.groups import group_ids_by_name
from app.retrieval.search import fulltext_search


def titles(hits):
    return {h.title for h in hits}


def test_a_user_only_gets_chunks_their_groups_may_read(engine, add_document):
    add_document("vpn-guide.md", "VPN guide", "internal",
                 "Restart the VPN client when the connection drops.")
    add_document("vpn-admin.md", "VPN admin runbook", "it_restricted",
                 "Rotate the VPN gateway certificate and reset the tunnel keys.")
    add_document("offboarding.md", "Offboarding checklist", "hr_confidential",
                 "Collect the laptop and revoke the VPN badge.")

    question = "rotate the VPN gateway certificate"
    employee = group_ids_by_name(engine, ["everyone"])
    helpdesk = group_ids_by_name(engine, ["everyone", "helpdesk"])
    hr = group_ids_by_name(engine, ["everyone", "hr"])

    # limit=100 is far above the corpus size, so "absent" means filtered, not cut off.
    assert titles(fulltext_search(engine, question, employee, limit=100)) == {"VPN guide"}
    assert titles(fulltext_search(engine, question, helpdesk, limit=100)) == {
        "VPN guide",
        "VPN admin runbook",
    }
    assert titles(fulltext_search(engine, question, hr, limit=100)) == {
        "VPN guide",
        "Offboarding checklist",
    }
    assert fulltext_search(engine, question, [], limit=100) == []  # no groups sees nothing


def test_a_retired_version_is_never_returned(engine, add_document):
    add_document("policy.md", "Lockout policy", "internal", 
                 "Accounts lock after five failed attempts.")
    add_document("policy.md", "Lockout policy", "internal",
                 "Accounts lock after three failed attempts.")

    hits = fulltext_search(
        engine, "accounts lock failed attempts", group_ids_by_name(engine, ["everyone"]), limit=100
    )
    texts = " ".join(h.text for h in hits)
    assert "three" in texts
    assert "five" not in texts


def test_an_exact_error_code_ranks_its_own_chunk_first(engine, add_document):
    add_document("e809.md", "VPN error 809", "internal",
                 "Error VPN-809 means the tunnel handshake failed. Check the certificate date.")
    add_document("e404.md", "VPN error 404", "internal",
                 "Error VPN-404 means the gateway is unreachable. Check the network cable.")

    hits = fulltext_search(engine, "VPN-809", group_ids_by_name(engine, ["everyone"]))
    assert hits[0].title == "VPN error 809"


def test_hostile_questions_are_harmless(engine, add_document):
    add_document("vpn.md", "VPN guide", "internal", "Restart the VPN client.")
    everyone = group_ids_by_name(engine, ["everyone"])

    for question in [
        "'; DROP TABLE chunks; --",
        "vpn' & !(a | b) <-> c:* ",
        "((((",
        "!!! ??? ...",
        "a" * 5000,
    ]:
        fulltext_search(engine, question, everyone, limit=100)  # must not raise

    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM chunks")).scalar_one() > 0