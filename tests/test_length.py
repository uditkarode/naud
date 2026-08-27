from collections.abc import Callable

import pytest

SPLIT = [
    (
        "I ran the tests, and they passed, but the build was slow, so I checked the cache and it was stale and huge.",
        "I ran the tests. They passed. But the build was slow, so I checked the cache. It was stale and huge.",
    ),
    (
        "The parser reads the text and applies the rules and then it writes the output to the file that you gave it on the command line.",
        "The parser reads the text and applies the rules. Then it writes the output to the file that you gave it on the command line.",
    ),
    ("I ran the tests, and they passed.", "I ran the tests, and they passed."),
]
PARAGRAPHS = [
    ("One. Two. Three. Four. Five. Six. Seven. Eight.", "One. Two. Three. Four.\n\nFive. Six. Seven. Eight."),
    ("One. Two. Three. Four. Five. Six.", "One. Two. Three. Four. Five. Six."),
]


@pytest.mark.parametrize(("text", "expected"), SPLIT + PARAGRAPHS)
def test_length(cleaned: Callable[[str], str], text: str, expected: str) -> None:
    assert cleaned(text) == expected


def test_a_long_sentence_with_nowhere_to_split_is_pointed_at(looks: Callable[[str], set[str]]) -> None:
    text = "The parser that reads the text from the file that you gave it on the command line writes the output to the terminal."
    assert "long" in looks(text)
    assert "long" not in looks("The parser writes the output.")
