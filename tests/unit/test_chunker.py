from app.retrieval.chunker import chunk_markdown

DOC = """\
Intro text before any heading.

# VPN
## Setup
Install the client.

## Troubleshooting
### Timeouts
Check your network.

# Printers
Restart the spooler.
"""


def test_chunks_follow_headings_and_never_cross_them():
    chunks = chunk_markdown(DOC)

    # Headings without body text produce no chunk. Siblings and parents reset the path.
    assert [(c.heading_path, c.text) for c in chunks] == [
        ("", "Intro text before any heading."),
        ("VPN > Setup", "Install the client."),
        ("VPN > Troubleshooting > Timeouts", "Check your network."),
        ("Printers", "Restart the spooler."),
    ]
    assert [c.ordinal for c in chunks] == [0, 1, 2, 3]


def test_hash_lines_inside_code_blocks_are_not_headings():
    fence = "`" * 3
    doc = (
        "## Restart\nRun this:\n\n"
        f"{fence}bash\n# restart the service\nsudo systemctl restart vpn\n{fence}\n"
    )
    chunks = chunk_markdown(doc)

    assert len(chunks) == 1
    assert chunks[0].heading_path == "Restart"
    assert "# restart the service" in chunks[0].text


def test_long_section_is_split_with_overlap_and_loses_no_text():
    steps = [f"Step {i}: do the thing carefully and confirm the result." for i in range(1, 31)]
    doc = "## Procedure\n" + "\n\n".join(steps)

    chunks = chunk_markdown(doc, max_chars=300, overlap=60)

    assert len(chunks) > 1
    assert all(c.heading_path == "Procedure" for c in chunks)
    assert all(len(c.text) <= 300 for c in chunks)
    # No step was lost at a split point.
    assert all(any(f"Step {i}:" in c.text for c in chunks) for i in range(1, 31))
    # Each chunk starts with text repeated from the end of the previous one.
    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert current.text[:20] in previous.text


def test_one_huge_paragraph_is_still_split_within_the_limit():
    doc = "## Log output\n" + " ".join(["word"] * 500)

    chunks = chunk_markdown(doc, max_chars=300, overlap=60)

    assert len(chunks) > 1
    assert all(len(c.text) <= 300 for c in chunks)
    assert sum(len(c.text.split()) for c in chunks) >= 500  # nothing truncated