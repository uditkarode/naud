from collections.abc import Callable

import pytest

EMPHASIS = [
    ("Honestly, the real problem is the actual parser.", "The problem is the parser."),
    ("That is genuinely the whole point.", "That is the point."),
    ("This is exactly what we need.", "This is what we need."),
    ("The right way to do this is simple.", "The way to do this is simple."),
    ("So you got lucky, but not really lucky.", "So you got lucky, but not quite lucky."),
    ("Real estate is very important.", "Real estate is very important."),
]
FILLER = [
    ("It's worth noting that the model works.", "The model works."),
    ("The honest answer is that it works.", "It works."),
    ("Great question! The point is that it works.", "It works."),
]
JARGON = [
    ("It leverages a robust model.", "It uses a model."),
    ("However, the whole approach compounds over time.", "But the approach grows over time."),
    ("Please utilize the tool in order to obtain the result prior to the meeting.", "Please use the tool to get the result before the meeting."),
    ("## Leverage the API", "## Use the API"),
]
LIVES = [
    ("The risk lives in the gap between them.", "The risk is in the gap between them."),
    ("My parents live in Tokyo.", "My parents live in Tokyo."),
    ("They live here.", "They live here."),
]
STRANDED = [
    ("the **real** problem", "the problem"),
    ("There are two genuinely-different routes.", "There are two different routes."),
    ("Playing straight at the TV is a perfectly real path.", "Playing straight at the TV is a path."),
]


@pytest.mark.parametrize(("text", "expected"), EMPHASIS + FILLER + JARGON + LIVES + STRANDED)
def test_words(cleaned: Callable[[str], str], text: str, expected: str) -> None:
    assert cleaned(text) == expected


@pytest.mark.parametrize(("text", "rule"), [
    ("The data is real.", "emphasis"),
    ('The word "real" is banned.', "emphasis"),
    ("Which brings me back to the parser.", "look"),
    ("This means the parser is slow.", "vague"),
])
def test_only_pointed_at(cleaned: Callable[[str], str], looks: Callable[[str], set[str]], text: str, rule: str) -> None:
    assert cleaned(text) == text
    assert rule in looks(text)


def test_a_bare_this_is_vague_but_a_determiner_is_not(looks: Callable[[str], set[str]]) -> None:
    assert "vague" in looks("This is where it gets interesting.")
    assert "vague" not in looks("That bug is old.")
