"""The leakage matrix, run on the FINAL retrieval function (hybrid search plus rerank).

For every user and every document, a query built from that document is run as that user.
The document must be returned if and only if the user may read it, and nothing else the user
may not read may ever be returned. Groups are read from the database on every query, like the
real auth dependency does.

HashEmbedder and OverlapReranker are test doubles: they exercise our filtering logic, not
semantic quality.
"""

import re

import pytest
from sqlalchemy import text

from app.db.seed import seed_demo_users
from app.db.users import get_user_by_email
from app.retrieval.embedder import HashEmbedder
from app.retrieval.retrieve import retrieve
from eval.leakage import Probe, run_matrix

USERS = ["alice@demo.local", "bob@demo.local", "carol@demo.local", "dave@demo.local"]
EVERYONE = set(USERS)
BOB, CAROL = "bob@demo.local", "carol@demo.local"

# (file, title, classification, a word that appears only in this document).
# The two VPN documents are a trap pair: they share keywords on purpose.
DOCS = [
    ("wifi.md", "Wi-Fi guide", "public", "zephyrnet"),
    ("vpn-guide.md", "VPN guide", "internal", "quillgate"),
    ("vpn-admin.md", "VPN admin runbook", "it_restricted", "ironlatch"),
    ("incident.md", "Incident response runbook", "security_restricted", "redflare"),
    ("offboarding.md", "Offboarding checklist", "hr_confidential", "lanternkey"),
]

# Who may read what. Written out by hand: it must not share code with what it checks.
READERS = {
    "wifi.md": EVERYONE,
    "vpn-guide.md": EVERYONE,
    "vpn-admin.md": {BOB, CAROL},
    "incident.md": {CAROL},
    "offboarding.md": {"dave@demo.local"},
}


class OverlapReranker:
    """Scores a chunk by how many of the question's words it contains. Deterministic."""

    model_name = "overlap-test-only"

    def score(self, query, texts):
        words = set(re.findall(r"[a-z0-9]+", query.lower()))
        return [float(len(words & set(re.findall(r"[a-z0-9]+", t.lower())))) for t in texts]


@pytest.fixture
def probes(engine, add_document):
    seed_demo_users(engine, "password-for-tests")
    for name, title, classification, token in DOCS:
        shared = (
            "Check the vpn tunnel and gateway certificate."
            if "vpn" in name
            else "Follow the steps."
        )
        add_document(name, title, classification, f"{token} is the key term here. {shared}")
    return [Probe(name, f"{title} {token}") for name, title, _, token in DOCS]


def check(engine, probes, readers):
    def fetch(email, question):
        user = get_user_by_email(engine, email)  # groups read fresh on every query
        hits = retrieve(engine, HashEmbedder(), OverlapReranker(), question, user.group_ids)
        return [hit.source_uri for hit in hits]

    return run_matrix(USERS, probes, fetch, lambda email, uri: email in readers[uri])


def assert_clean(result):
    assert result.pairs == len(USERS) * len(DOCS)
    assert result.leaks == []
    assert result.misses == []


def test_baseline(engine, probes):
    assert_clean(check(engine, probes, READERS))


def test_after_an_acl_change(engine, probes):
    with engine.begin() as conn:
        conn.execute(  # grant the helpdesk group read access to the security runbook
            text(
                "INSERT INTO document_acl (document_id, group_id)"
                " SELECT d.id, g.id FROM documents d, groups g"
                " WHERE d.source_uri = 'incident.md' AND g.name = 'helpdesk'"
            )
        )
        conn.execute(  # remove every group from the Wi-Fi guide: no ACL means invisible to all
            text(
                "DELETE FROM document_acl"
                " WHERE document_id = (SELECT id FROM documents WHERE source_uri = 'wifi.md')"
            )
        )
    readers = {**READERS, "incident.md": {BOB, CAROL}, "wifi.md": set()}
    assert_clean(check(engine, probes, readers))


def test_after_a_retire(engine, probes):
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE documents SET status = 'retired', retired_at = now()"
                " WHERE source_uri = 'offboarding.md'"
            )
        )
    assert_clean(check(engine, probes, {**READERS, "offboarding.md": set()}))


def test_after_a_group_removal(engine, probes):
    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM user_groups"
                " WHERE user_id = (SELECT id FROM users WHERE email = 'bob@demo.local')"
                " AND group_id = (SELECT id FROM groups WHERE name = 'helpdesk')"
            )
        )
    assert_clean(check(engine, probes, {**READERS, "vpn-admin.md": {CAROL}}))