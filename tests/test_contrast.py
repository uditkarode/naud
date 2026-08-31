from collections.abc import Callable

import pytest

CLEFT = [
    ("It's not just about speed, but about trust.", "It's about trust."),
    ("It's not just about speed, it's about trust.", "It's about trust."),
    ("not only fast but also correct", "correct"),
    ("It's not for everyone, but it works.", "It's not for everyone, but it works."),
]
TAIL = [
    ("I verified it rather than guessing.", "I verified it (not: guess)."),
    ("It will clone rather than rebuild.", "It will clone (not: rebuild)."),
    ("It clones rather than rebuilding.", "It clones (not: rebuild)."),
    ("Exhaustion hangs forever instead of erroring.", "Exhaustion hangs forever (not: error)."),
    ("It stayed alive instead of being destroyed.", "It stayed alive (not: destroyed)."),
    ("It starts a run normally, instead of failing.", "It starts a run normally (not: fail)."),
    ("Rather than guessing, verify it.", "Verify it."),
    ("It is measured, not guessed.", "It is measured (not: guessed)."),
    ("It is measured, not guessed, and it is fast.", "It is measured (not: guessed), and it is fast."),
    ("The code is simple and not clever.", "The code is simple (not: clever)."),
    ("It uses a model rather than a simple one.", "It uses a model (not: a simple one)."),
    ("The size is 1 byte instead of 848.", "The size is 1 byte (not: 848)."),
    ("Use spaCy instead of NLTK for this.", "Use spaCy instead of NLTK for this."),
]
STACCATO = [
    ("No fluff. No hype. Just results.", "Results."),
    ("No fluff, no hype, just results.", "Results."),
]
NOT_BUT = [
    ("This isn't a bug. It's a feature.", "It's a feature."),
    ("This isn't about speed. It's about trust.", "It's about trust."),
    ("The problem was never the parser. The problem was the data.", "The problem was the data."),
    ("He is not here. It is late.", "He is not here. It is late."),
]
NOT_THAT = [
    ("Not that the parser is slow. It isn't.", ""),
    ("Not that I know of.", "Not that I know of."),
]


@pytest.mark.parametrize(("text", "expected"), CLEFT + TAIL + STACCATO + NOT_BUT + NOT_THAT)
def test_contrast(cleaned: Callable[[str], str], text: str, expected: str) -> None:
    assert cleaned(text) == expected


@pytest.mark.parametrize("text", ["It's not for everyone, but it works.", "Use spaCy instead of NLTK for this."])
def test_unsure_contrasts_are_only_pointed_at(looks: Callable[[str], set[str]], text: str) -> None:
    assert looks(text) & {"cleft", "tail"}
