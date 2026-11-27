from eval.leakage import Probe, run_matrix

PROBES = [Probe("a.md", "query a"), Probe("b.md", "query b")]
READERS = {"a.md": {"u1", "u2"}, "b.md": {"u1"}}


def may_read(user, uri):
    return user in READERS[uri]


def test_the_matrix_flags_leaks_and_silent_blocking_and_passes_a_correct_retrieval():
    users = ["u1", "u2"]

    def correct(user, question):
        return [uri for uri in READERS if may_read(user, uri)]

    def leaky(user, question):  # ignores permissions
        return ["a.md", "b.md"]

    def silent(user, question):  # returns nothing: zero leaks, but useless
        return []

    ok = run_matrix(users, PROBES, correct, may_read)
    assert (ok.pairs, ok.leaks, ok.misses) == (4, [], [])

    bad = run_matrix(users, PROBES, leaky, may_read)
    assert bad.leaks == [("u2", "a.md", "b.md"), ("u2", "b.md", "b.md")]
    assert bad.misses == []

    nothing = run_matrix(users, PROBES, silent, may_read)
    assert nothing.leaks == []
    assert nothing.misses == [("u1", "a.md"), ("u1", "b.md"), ("u2", "a.md")]