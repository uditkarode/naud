"""Text in, text out."""
import re
from collections.abc import Callable, Iterator
from itertools import takewhile

from spacy.tokens import Doc

from .core import Edit, nlp
from .rules import RULES

Mend = tuple[str, str | Callable[[re.Match[str]], str]]

FENCE = re.compile(r"```.*?```", re.S)
INLINE = re.compile(r"(`[^`\n]*`)")
PREFIX = re.compile(r"[ \t]*(?:(?:[-*+]|\d+[.)]|#{1,6}|>)[ \t]+)*")
CURLY = str.maketrans("’“”", "'\"\"")
LOWER = r"([a-z])(?=[a-z]*(?:\W|$))"
ARTICLE = re.compile(r"\b[Aa]n? $")
MEND: list[Mend] = [(r" +([,.;:!?)])", r"\1"), (r"[,;:]+(?=[,;:.!?])", ""), (r" {2,}", " ")]


def blank(m: re.Match[str]) -> str:
    """The same length, with nothing to parse."""
    return re.sub(r"\S", " ", m.group())


def lines(text: str) -> Iterator[tuple[int, str]]:
    """(offset, line) for every line of prose: outside code fences, past any markdown bullet or heading."""
    for m in re.finditer(r".+", FENCE.sub(blank, text)):
        prose = PREFIX.sub("", m.group(), count=1)
        if prose.strip():
            yield m.end() - len(prose), prose


def edits(doc: Doc) -> list[Edit]:
    """Every rule's edits, earlier rules winning where they overlap."""
    kept: list[Edit] = []
    for rule in RULES:
        for e in sorted(rule(doc), key=lambda e: (e.start, -e.end)):
            if not any(e.yields_to(k) for k in kept):
                kept.append(e)
    return sorted((e for e in kept if e.text != doc.text[e.start : e.end]), key=lambda e: e.start)


def found(line: str) -> list[Edit]:
    """Edits for one line of prose, with inline code blanked so it can't be touched."""
    return edits(nlp(INLINE.sub(blank, line).translate(CURLY)))


def article(rest: str) -> str:
    """The article for the word that opens `rest`."""
    word = "".join(takewhile(str.isalnum, rest)).lower()
    vowel = word[:1] in "aeiou" and not word.startswith(("one", "uni", "use", "eu"))
    return "an" if vowel or word.startswith(("hour", "honest", "heir", "honor")) else "a"


def recase(line: str, at: int) -> str:
    """Capitalize the word at `at`, if it's a plain lowercase word."""
    return line[:at] + re.sub("^" + LOWER, lambda m: m[1].upper(), line[at:], count=1)


def rearticle(line: str, at: int) -> str:
    """Check an "a"/"an" right before `at` against the word that now follows it."""
    an = ARTICLE.search(line[:at])
    if not an:
        return line
    fixed = article(line[at:])
    return line[: an.start()] + (fixed.capitalize() if an[0][0] == "A" else fixed) + " " + line[at:]


def apply(line: str, edits: list[Edit]) -> str:
    """Right to left, so offsets stay true. A cut hands its capital letter to the next word."""
    for e in reversed(edits):
        if e.text is None:
            continue
        was, line = line[e.start : e.end], line[: e.start] + e.text + line[e.end :]
        if e.text.endswith(". ") or (e.text == "" and was[:1].isupper()):
            line = recase(line, e.start + len(e.text))
        if e.text == "":
            line = rearticle(line, e.start)
    return line


def tidy(line: str) -> str:
    """Mend what the cuts left: spaces before marks, doubled marks, a mark with nothing before it. Code stays as is."""

    def prose(s: str) -> str:
        for old, new in MEND:
            s = re.sub(old, new, s)
        return s

    line = "".join(p if i % 2 else prose(p) for i, p in enumerate(INLINE.split(line)))
    return re.sub(r"^[,;:]+ *", "", line)


def lint(text: str) -> list[Edit]:
    """Every edit naud would make, with offsets into the text."""
    return [e.shift(at) for at, line in lines(text) for e in found(line)]


def clean(text: str) -> str:
    """A paragraph broken in two keeps its indent, so a bullet's second half stays in the bullet."""
    out: list[str] = []
    at = 0
    for start, line in lines(text):
        indent = " " * (start - text.rfind("\n", 0, start) - 1)
        out += text[at:start], tidy(apply(line, found(line))).replace("\n\n", "\n\n" + indent)
        at = start + len(line)
    return "".join(out) + text[at:]
