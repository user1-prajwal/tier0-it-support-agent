from collections.abc import Sequence

from sqlalchemy import Engine, text


def group_ids_by_name(engine: Engine, names: Sequence[str]) -> list[int]:
    """Turn group names into ids. A typo raises instead of silently shrinking access."""
    wanted = set(names)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name FROM groups WHERE name = ANY(:names)"),
            {"names": list(wanted)},
        ).all()
    missing = wanted - {row.name for row in rows}
    if missing:
        raise ValueError(f"unknown group names: {sorted(missing)}")
    return sorted(row.id for row in rows)

def group_names_by_id(engine: Engine, ids: Sequence[int]) -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT name FROM groups WHERE id = ANY(CAST(:ids AS bigint[])) ORDER BY name"),
            {"ids": list(ids)},
        )
        return list(rows.scalars())