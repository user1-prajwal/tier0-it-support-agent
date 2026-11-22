"""Read one document file: front matter plus body.

Front matter is TOML between two +++ lines (Python's standard library parses it):

    +++
    title = "VPN troubleshooting"
    classification = "internal"
    synthetic = true
    +++
    # VPN ...
"""

import tomllib
from dataclasses import dataclass

# Which groups may read a document, by classification. Retrieval trusts the document_acl
# rows written from this table, so a mistake here is a permission bug. Keep it small.
CLASSIFICATION_GROUPS: dict[str, list[str]] = {
    "public": ["everyone"],
    "internal": ["everyone"],
    "it_restricted": ["helpdesk", "security"],
    "security_restricted": ["security"],
    "hr_confidential": ["hr"],
}

_REQUIRED = {"title", "classification", "synthetic"}
_OPTIONAL = {"license_note"}


class DocumentError(ValueError):
    """A document cannot be ingested: bad front matter or no text."""


@dataclass(frozen=True)
class ParsedDocument:
    title: str
    classification: str
    synthetic: bool
    license_note: str | None
    body: str


def parse_document(text: str) -> ParsedDocument:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        raise DocumentError("the file must start with a +++ front matter block")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "+++"), None)
    if end is None:
        raise DocumentError("the front matter block is not closed with +++")

    try:
        meta = tomllib.loads("\n".join(lines[1:end]))
    except tomllib.TOMLDecodeError as exc:
        raise DocumentError(f"front matter is not valid TOML: {exc}") from exc

    missing = _REQUIRED - meta.keys()
    unknown = meta.keys() - _REQUIRED - _OPTIONAL
    if missing:
        raise DocumentError(f"missing front matter keys: {sorted(missing)}")
    if unknown:
        raise DocumentError(f"unknown front matter keys: {sorted(unknown)}")

    title, classification, synthetic = meta["title"], meta["classification"], meta["synthetic"]
    if not isinstance(title, str) or not title.strip():
        raise DocumentError("title must be a non-empty string")
    if not isinstance(classification, str) or classification not in CLASSIFICATION_GROUPS:
        raise DocumentError(f"classification must be one of {sorted(CLASSIFICATION_GROUPS)}")
    if not isinstance(synthetic, bool):
        raise DocumentError("synthetic must be true or false")
    license_note = meta.get("license_note")
    if not synthetic and not license_note:
        raise DocumentError("a document that is not synthetic needs a license_note")

    return ParsedDocument(
        title.strip(),
        classification,
        synthetic,
        license_note,
        "\n".join(lines[end + 1 :]),
    )