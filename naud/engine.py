"""Text in, text out."""
from spacy.tokens import Doc

from .edit import Edit, Kind
from .markdown import as_plain, ends_fenced, lines
from .mend import rearticle, recase, tidy
from .parse import parse
from .rules import RULES


def edits(doc: Doc) -> list[Edit]:
    """Every rule's edits, earlier rules winning where they overlap. A KEEP blocks the others, then leaves."""
    kept: list[Edit] = []
    for rule in RULES:
        for edit in sorted(rule.find(doc), key=lambda e: (e.start, -e.end)):
            edit = edit._replace(rule=rule.name)
            if not any(edit.yields_to(k) for k in kept):
                kept.append(edit)
    return sorted((e for e in kept if e.kind is not Kind.KEEP), key=lambda e: e.start)


def found(line: str) -> list[Edit]:
    return edits(parse(as_plain(line)))


def apply(line: str, edits: list[Edit]) -> str:
    """Right to left, so offsets stay true. A cut hands its capital to the next word and rechecks the article before it."""
    for e in reversed(edits):
        if e.kind is Kind.LOOK:
            continue
        was, line = line[e.start : e.end], line[: e.start] + e.text + line[e.end :]
        if e.kind is Kind.STOP or (e.kind is Kind.CUT and was[:1].isupper()):
            line = recase(line, e.start + len(e.text))
        if e.kind is Kind.CUT:
            line = rearticle(line, e.start)
    return line


def lint(text: str) -> list[Edit]:
    """Every edit naud would make, with offsets into the text."""
    return [e.shift(at) for at, line in lines(text) for e in found(line)]


def clean(text: str, fenced: bool = False) -> str:
    """The text with every edit made. `fenced` says the text opens inside a code fence.
    A paragraph broken in two keeps its indent, so a bullet's second half stays in the bullet."""
    out: list[str] = []
    at = 0
    for start, line in lines(text, fenced):
        indent = " " * (start - text.rfind("\n", 0, start) - 1)
        out += text[at:start], tidy(apply(line, found(line))).replace("\n\n", "\n\n" + indent)
        at = start + len(line)
    return "".join(out) + text[at:]


class Stream:
    """Cleans text as it arrives, in batches of whole lines, remembering an open code fence between batches."""

    def __init__(self) -> None:
        self.fenced = False

    def feed(self, text: str) -> str:
        cleaned = clean(text, self.fenced)
        self.fenced = ends_fenced(text, self.fenced)
        return cleaned
