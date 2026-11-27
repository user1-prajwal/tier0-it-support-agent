"""The leakage matrix: every user x every document. Pure logic, no database.

For each pair, a query built from the document is run as that user. Two things are checked:
- LEAK: a returned result belongs to a document the user may not read. Checked on EVERYTHING
  returned, not just the targeted document. The target must be exactly zero.
- MISS: the targeted document IS readable by the user but was not returned. A retrieval that
  returns nothing has zero leaks, so misses must be checked too.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Probe:
    source_uri: str  # the document this query was built from
    query: str


@dataclass(frozen=True)
class MatrixResult:
    pairs: int
    leaks: list[tuple[str, str, str]]  # (user, probed document, leaked document)
    misses: list[tuple[str, str]]  # (user, readable document that was not returned)


def run_matrix(
    users: Sequence[str],
    probes: Sequence[Probe],
    fetch: Callable[[str, str], list[str]],  # (user, question) -> source_uris returned
    may_read: Callable[[str, str], bool],  # (user, source_uri) -> ground truth
) -> MatrixResult:
    leaks: list[tuple[str, str, str]] = []
    misses: list[tuple[str, str]] = []
    for user in users:
        for probe in probes:
            returned = fetch(user, probe.query)
            for uri in dict.fromkeys(returned):  # each document once, in order
                if not may_read(user, uri):
                    leaks.append((user, probe.source_uri, uri))
            if may_read(user, probe.source_uri) and probe.source_uri not in returned:
                misses.append((user, probe.source_uri))
    return MatrixResult(len(users) * len(probes), leaks, misses)