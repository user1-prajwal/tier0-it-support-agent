"""Split Markdown into chunks that follow its headings.

Rules (from the build brief):
- A chunk never crosses a heading.
- A short section is one chunk. A long section is split at paragraph boundaries, and
  consecutive pieces overlap by a few characters. There is never overlap across headings.
- heading_path records where the chunk lives, e.g. "VPN > Troubleshooting".

Limits: only "#" style headings are recognised, and a long code block can be split
across two chunks.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    heading_path: str
    text: str

    @property
    def embedding_text(self) -> str:
        """What gets embedded: the heading path gives a short chunk its topic."""
        return f"{self.heading_path}\n{self.text}" if self.heading_path else self.text


def chunk_markdown(markdown: str, *, max_chars: int = 1000, overlap: int = 120) -> list[Chunk]:
    if overlap < 0 or overlap * 2 >= max_chars:
        raise ValueError("overlap must be at least 0 and less than half of max_chars")

    chunks: list[Chunk] = []
    for heading_path, body in _sections(markdown):
        body = body.strip()
        if not body:
            continue  # a heading with nothing under it
        for text in _split_section(body, max_chars, overlap):
            chunks.append(Chunk(ordinal=len(chunks), heading_path=heading_path, text=text))
    return chunks


def _sections(markdown: str) -> Iterator[tuple[str, str]]:
    """Yield (heading_path, body) for the text before the first heading and each section."""
    stack: list[tuple[int, str]] = []  # (heading level, title) of the open headings
    heading_path = ""
    lines: list[str] = []
    in_fence = False

    for line in markdown.splitlines():
        if _FENCE.match(line):
            in_fence = not in_fence
        match = None if in_fence else _HEADING.match(line)

        if match is None:
            lines.append(line)
            continue

        yield heading_path, "\n".join(lines)
        level, title = len(match.group(1)), match.group(2).strip()
        while stack and stack[-1][0] >= level:
            stack.pop()  # a sibling or a higher-level heading closes the deeper ones
        stack.append((level, title))
        heading_path = " > ".join(t for _, t in stack)
        lines = []

    yield heading_path, "\n".join(lines)


def _split_section(body: str, max_chars: int, overlap: int) -> list[str]:
    if len(body) <= max_chars:
        return [body]

    # Reserve room for the overlap and the blank line, so no chunk can exceed max_chars.
    piece_limit = max_chars - overlap - 2
    pieces: list[str] = []
    for paragraph in re.split(r"\n\s*\n", body):
        if paragraph.strip():
            pieces.extend(_split_long(paragraph.strip(), piece_limit))

    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = f"{current}\n\n{piece}" if current else piece
        if len(candidate) <= max_chars:
            current = candidate
            continue
        chunks.append(current)
        tail = _tail(current, overlap)
        current = f"{tail}\n\n{piece}" if tail else piece
    chunks.append(current)
    return chunks


def _split_long(paragraph: str, limit: int) -> list[str]:
    """Cut a paragraph that is longer than the limit, preferring line then word boundaries."""
    pieces: list[str] = []
    while len(paragraph) > limit:
        cut = paragraph.rfind("\n", 0, limit + 1)
        if cut <= 0:
            cut = paragraph.rfind(" ", 0, limit + 1)
        if cut <= 0:
            cut = limit  # no whitespace at all: hard cut
        pieces.append(paragraph[:cut].strip())
        paragraph = paragraph[cut:].strip()
    if paragraph:
        pieces.append(paragraph)
    return pieces


def _tail(text: str, overlap: int) -> str:
    """The last `overlap` characters of text, starting at a word boundary."""
    if overlap == 0:
        return ""
    if len(text) <= overlap:
        return text.strip()
    tail = text[-overlap:]
    if not text[-overlap - 1].isspace():  # we cut a word in half: drop the partial word
        parts = tail.split(None, 1)
        tail = parts[1] if len(parts) == 2 else ""
    return tail.strip()