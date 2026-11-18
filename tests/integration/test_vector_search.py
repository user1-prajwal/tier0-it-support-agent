"""Does the dense-search chain work on a real pgvector?

HashEmbedder vector -> vector(384) column -> cosine-distance ordering.
HashEmbedder is test-only, so this proves the plumbing, not semantic quality.
"""

from sqlalchemy import text

from app.retrieval.embedder import HashEmbedder

INSERT = text("INSERT INTO probe VALUES (:name, CAST(:embedding AS vector))")
SEARCH = text("SELECT name FROM probe ORDER BY embedding <=> CAST(:query AS vector)")


def to_pgvector(vector: list[float]) -> str:
    return "[" + ",".join(repr(x) for x in vector) + "]"


def test_cosine_search_returns_the_closest_text_first(engine):
    embedder = HashEmbedder()
    texts = {
        "vpn": "vpn keeps disconnecting",
        "password": "reset my password",
        "printer": "printer toner replacement",
    }
    query = embedder.embed_query("how do I reset a password")

    with engine.begin() as conn:
        # TEMP table: it vanishes with the connection, so we leave nothing behind.
        conn.execute(text("CREATE TEMP TABLE probe (name text, embedding vector(384))"))
        for name, content in texts.items():
            vector = to_pgvector(embedder.embed_query(content))
            conn.execute(INSERT, {"name": name, "embedding": vector})
        ranked = conn.execute(SEARCH, {"query": to_pgvector(query)}).scalars().all()

    assert ranked[0] == "password"