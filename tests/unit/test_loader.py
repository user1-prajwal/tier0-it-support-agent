import pytest

from app.ingest.loader import DocumentError, parse_document

GOOD = (
    '+++\ntitle = "VPN troubleshooting"\nclassification = "internal"\nsynthetic = true\n+++\n'
    "# VPN\nCheck the client.\n"
)


def test_valid_document_is_parsed():
    doc = parse_document(GOOD)
    assert doc.title == "VPN troubleshooting"
    assert doc.classification == "internal"
    assert doc.synthetic is True
    assert doc.body.startswith("# VPN")


@pytest.mark.parametrize(
    "front_matter",
    [
        'title = "T"\nclassification = "confidential"\nsynthetic = true',
        'title = "T"\nclassifcation = "internal"\nsynthetic = true',
        'title = "T"\nclassification = "internal"\nsynthetic = false',
    ],
    ids=["unknown-classification", "misspelled-key", "no-licence-note"],
)
def test_bad_front_matter_is_rejected(front_matter):
    with pytest.raises(DocumentError):
        parse_document(f"+++\n{front_matter}\n+++\nBody text.\n")