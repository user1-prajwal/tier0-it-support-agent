from app.db.groups import group_ids_by_name
from app.retrieval.embedder import HashEmbedder
from app.retrieval.search import hybrid_search


def test_hybrid_fuses_both_arms_and_never_returns_unreadable_chunks(engine, add_document):
    add_document("vpn-guide.md", "VPN guide", "internal",
                 "Restart the VPN client when the connection drops.")
    add_document("printers.md", "Printer guide", "internal",
                 "Replace the toner cartridge when the light is red.")
    add_document("vpn-admin.md", "VPN admin runbook", "it_restricted",
                 "Rotate the VPN gateway certificate and reset the tunnel keys.")

    everyone = group_ids_by_name(engine, ["everyone"])
    hits = hybrid_search(engine, HashEmbedder(), "rotate the VPN gateway certificate", everyone)

    # The restricted runbook is the best match, but this user may not read it.
    assert [h.title for h in hits] == ["VPN guide", "Printer guide"]
    # The VPN guide is found by both arms. The printer guide by the dense arm only.
    assert hits[0].fulltext_rank == 1 and hits[0].dense_rank is not None
    assert hits[1].fulltext_rank is None and hits[1].dense_rank is not None