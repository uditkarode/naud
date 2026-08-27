from collections.abc import Callable

import pytest

from naud import Edit, Kind, Stream, clean, lint
from naud.markdown import ends_fenced


@pytest.mark.parametrize(("text", "expected"), [
    ("```\nreal = actual = 1\n```", "```\nreal = actual = 1\n```"),
    ("```\nreal = 1\n", "```\nreal = 1\n"),
    ("  ~~~\n  real = 1\n  ~~~\n  It is really good.", "  ~~~\n  real = 1\n  ~~~\n  It is good."),
    ("```real```\nIt is really good.", "```real```\nIt is good."),
    ("It’s worth noting that the `real` flag is real.", "The `real` flag is real."),
    ("It is genuinely fast.\r\n", "It is fast.\r\n"),
    ("", ""),
    ("- honestly, yes", "- yes"),
    ("An actual problem.", "A problem."),
    ("a robust, seamless integration", "an integration"),
    ("Honestly, the real problem is the actual parser: it leverages a robust model.", "The problem is the parser. It uses a model."),
    (
        "- We shipped it. Honestly it works. Great question. Really, it is robust. It is not slow. It is fast. Done. Truly done.",
        "- We shipped it. It works. It is robust.\n\n  It is fast. Done. Done.",
    ),
])
def test_clean(text: str, expected: str) -> None:
    assert clean(text) == expected


def test_lint_has_offsets_into_the_whole_text() -> None:
    assert lint("# Title\n\nHonestly, it works.") == [Edit(9, 19, Kind.CUT, "", "emphasis")]


def test_a_kept_phrase_leaves_no_trace() -> None:
    assert lint("Real estate.") == []


def test_a_stream_remembers_an_open_fence() -> None:
    stream = Stream()
    assert [stream.feed(t) for t in ("```\n", "very = 1\n", "```\nvery good\n")] == ["```\n", "very = 1\n", "```\ngood\n"]


@pytest.mark.parametrize(("text", "fenced", "expected"), [
    ("```\n", False, True),
    ("```\n", True, False),
    ("```\nx\n```\n", False, False),
    ("x\n", True, True),
])
def test_ends_fenced(text: str, fenced: bool, expected: bool) -> None:
    assert ends_fenced(text, fenced) is expected
