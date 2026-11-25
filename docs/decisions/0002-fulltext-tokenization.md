# 0002: Full-text queries are tokenized by Postgres, not by a Python regex

Date: 2026-11-25. Status: accepted. Changes brief Section 4 (keyword search).

## Problem
The brief builds the tsquery in Python from `[a-z0-9]+` tokens. Postgres's parser indexes
`VPN-809` as `vpn` and `-809`, and `vpn.demo.local` as one host token. The Python query
`vpn | 809` therefore never matched the code, and `vpn | demo | local` never matched the host.
Found by a manual sanity check, then reproduced by two failing tests.

## Evidence (psql on the dev database)
- `to_tsvector('english', 'Error VPN-809 means ...')` contains `'-809'` and `'vpn'`.
- A query for bare `809` does not match it.
- `plainto_tsquery` keeps `-809`, `vpn.demo.local` and `bob@demo.local` as single terms.
- Query operators in the text are ignored. A 5000-character word is ignored with a notice.

## Decision
Use `plainto_tsquery('english', :question)` and rewrite AND as OR in SQL. The question stays a
bound parameter. NUL bytes are replaced by spaces. Removed: `build_or_query` and its caps.

## Rejected
Keeping the Python extractor and adding whole-token candidates for hosts, emails and signed
numbers: it re-implements part of the Postgres parser.

## Known limit
A user who types `809` without the hyphen will not match a document that wrote `VPN-809`,
because the index holds `-809`. The dense arm may still find it. Not changed until measured.
The question length cap belongs to the API layer (Phase 3).