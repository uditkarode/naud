"""Mends what the edits leave behind, from stray spaces and marks to articles and capitals."""
import re
from collections.abc import Callable
from itertools import takewhile

from .markdown import pieces

Mend = tuple[str, str | Callable[[re.Match[str]], str]]

LOWERCASE_WORD = r"([a-z])(?=[a-z]*(?:\W|$))"
ARTICLE = re.compile(r"\b[Aa]n? $")
MENDS: list[Mend] = [
    (r" +([,.;:!?)])", r"\1"),  # no space before a mark
    (r"[,;:]+(?=[,;:.!?])", ""),  # no mark right before another
    (r" {2,}", " "),
]


def tidy(line: str) -> str:
    """Mend the prose of a line, leave its code alone, and drop a mark left with nothing before it."""

    def mend(prose: str) -> str:
        for old, new in MENDS:
            prose = re.sub(old, new, prose)
        return prose

    line = "".join(piece if i % 2 else mend(piece) for i, piece in enumerate(pieces(line)))
    return re.sub(r"^[,;:]+ *", "", line)


def article(rest: str) -> str:
    """The article for the word that opens `rest`."""
    word = "".join(takewhile(str.isalnum, rest)).lower()
    vowel = word[:1] in "aeiou" and not word.startswith(("one", "uni", "use", "eu"))
    return "an" if vowel or word.startswith(("hour", "honest", "heir", "honor")) else "a"


def recase(line: str, at: int) -> str:
    """Capitalize the word at `at`, if it is a plain lowercase word."""
    return line[:at] + re.sub("^" + LOWERCASE_WORD, lambda m: m[1].upper(), line[at:], count=1)


def rearticle(line: str, at: int) -> str:
    """Check an "a"/"an" right before `at` against the word that now follows it."""
    an = ARTICLE.search(line[:at])
    if not an:
        return line
    fixed = article(line[at:])
    return line[: an.start()] + (fixed.capitalize() if an[0][0] == "A" else fixed) + " " + line[at:]
