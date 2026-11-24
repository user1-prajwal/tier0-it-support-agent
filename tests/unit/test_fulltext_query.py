from app.retrieval.search import build_or_query


def test_keywords_become_a_deduplicated_or_query():
    query = build_or_query("How do I reset my VPN password? VPN!")
    assert query == "how | do | i | reset | my | vpn | password"


def test_hostile_text_cannot_inject_query_syntax():
    query = build_or_query("vpn' & !(drop) | <-> :* ; -- \"x\" \\ %")
    # Only letters, digits, spaces and our own | operator may survive.
    assert set(query) <= set("abcdefghijklmnopqrstuvwxyz0123456789 |")
    assert build_or_query("!!! ???") is None  # nothing searchable: no query is run
    assert build_or_query("a" * 5000) is None  # an absurd token is dropped