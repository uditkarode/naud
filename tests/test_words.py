from collections.abc import Callable

import pytest

from naud import lint

EMPHASIS = [
    ("Honestly, the real problem is the actual parser.", "The problem is the parser."),
    ("That is genuinely the whole point.", "That is the point."),
    ("This is exactly what we need.", "This is what we need."),
    ("The right way to do this is simple.", "The way to do this is simple."),
    ("So you got lucky, but not really lucky.", "So you got lucky, but not quite lucky."),
    ("Real estate is very important.", "Real estate is very important."),
    ("Per-output delay forces exactly this shape.", "Per-output delay forces this shape."),
    ("Your diagnosis was exactly right.", "Your diagnosis was right."),
    ("I checked exactly one file.", "I checked exactly one file."),
    ("It is completely buried, but not entirely.", "It is buried, but not quite."),
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
    ("Reconcile compares the string against itself and doesn't churn.", "Reconcile compares the string against itself and doesn't change."),
    ("Less code churn means fewer bugs.", "Less code change means fewer bugs."),
    ("Customer churn is high.", "Customer churn is high."),
    ("It churns out code.", "It produces code."),
    ("The C trees are identical to what you have.", "The C trees are the same as what you have."),
    ("The trees are identical.", "The trees are the same."),
    ("It makes an identical copy.", "It makes the same copy."),
    ("Two identical copies.", "Two identical copies."),
    ("Output is byte-identical to before.", "Output is byte-identical to before."),
    ("BT currently plays late, as LDAC typically does.", "BT now plays late, as LDAC usually does."),
    ("The rate adjustment needs to converge.", "The rate adjustment needs to settle."),
    ("It predates the speaker.", "It comes before the speaker."),
    ("Just say the word and I'll do it.", "Just tell me and I'll do it."),
    ("Say the word on the timeout and I'll fix it.", "Tell me about the timeout and I'll fix it."),
]
LIVES = [
    ("The risk lives in the gap between them.", "The risk is in the gap between them."),
    ("My parents live in Tokyo.", "My parents live in Tokyo."),
    ("They live here.", "They live here."),
    ("BT sits at 0ms.", "BT is at 0ms."),
    ("Your 56 sits between 38 and 65.", "Your 56 is between 38 and 65."),
    ("The value has sat at zero.", "The value has been at zero."),
    ("Sit here.", "Sit here."),
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


def test_half_a_hyphenated_word_is_kept() -> None:
    assert lint("It is near-identical.") == []


def test_a_bare_this_is_vague_but_a_determiner_is_not(looks: Callable[[str], set[str]]) -> None:
    assert "vague" in looks("This is where it gets interesting.")
    assert "vague" not in looks("That bug is old.")
