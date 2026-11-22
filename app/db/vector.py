def to_pgvector(vector: list[float]) -> str:
    """Format a vector as pgvector's text literal, e.g. [0.1,0.2]. Used with CAST(... AS vector)."""
    return "[" + ",".join(repr(x) for x in vector) + "]"