from app.db.groups import group_ids_by_name
from app.ingest.pipeline import ingest_file
from app.retrieval.embedder import HashEmbedder
from app.retrieval.search import dense_search

TEMPLATE = """\
+++
title = "{title}"
classification = "{classification}"
synthetic = true
+++
# Topic
## Section
{body}
"""


def add(root, engine, name, title, classification, body):
    path = root / name
    path.write_text(TEMPLATE.format(title=title, classification=classification, body=body))
    ingest_file(engine, path, root, HashEmbedder())


def test_a_user_only_gets_chunks_their_groups_may_read(engine, clean_db, tmp_path):
    add(tmp_path, engine, "vpn-guide.md", "VPN guide", "internal",
        "Restart the VPN client when the connection drops.")
    add(tmp_path, engine, "vpn-admin.md", "VPN admin runbook", "it_restricted",
        "Rotate the VPN gateway certificate and reset the tunnel keys.")
    add(tmp_path, engine, "offboarding.md", "Offboarding checklist", "hr_confidential",
        "Collect the laptop and revoke the badge.")

    query = HashEmbedder().embed_query("rotate the VPN gateway certificate")
    employee = group_ids_by_name(engine, ["everyone"])
    helpdesk = group_ids_by_name(engine, ["everyone", "helpdesk"])

    # limit=100 is far above the corpus size, so "absent" means filtered, not cut off.
    employee_hits = dense_search(engine, query, employee, limit=100)
    helpdesk_hits = dense_search(engine, query, helpdesk, limit=100)

    assert {h.title for h in employee_hits} == {"VPN guide"}
    assert {h.title for h in helpdesk_hits} == {"VPN guide", "VPN admin runbook"}
    assert helpdesk_hits[0].title == "VPN admin runbook"  # closest first
    assert dense_search(engine, query, [], limit=100) == []  # no groups sees nothing


def test_a_retired_version_is_never_returned(engine, clean_db, tmp_path):
    add(tmp_path, engine, "policy.md", "Lockout policy", "internal",
        "Accounts lock after five failed attempts.")
    add(tmp_path, engine, "policy.md", "Lockout policy", "internal",
        "Accounts lock after three failed attempts.")

    query = HashEmbedder().embed_query("accounts lock after failed attempts")
    hits = dense_search(engine, query, group_ids_by_name(engine, ["everyone"]), limit=100)

    texts = " ".join(h.text for h in hits)
    assert "three" in texts
    assert "five" not in texts