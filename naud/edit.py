"""What an edit is, and how a span becomes one."""
from collections.abc import Callable, Iterable
from enum import Enum
from typing import NamedTuple, Self

from lemminflect import getInflection
from spacy.tokens import Doc, Span, Token


class Kind(Enum):
    CUT = "cut"  # the span goes
    SAY = "say"  # the span is said another way
    STOP = "stop"  # a full stop goes in, so the next word gets a capital
    LOOK = "look"  # naud can't fix this blindly, so it only points at it
    KEEP = "keep"  # the span stays, and nothing else may touch it


class Edit(NamedTuple):
    start: int
    end: int
    kind: Kind
    text: str = ""
    rule: str = ""

    def shift(self, by: int) -> Self:
        return self._replace(start=self.start + by, end=self.end + by)

    def yields_to(self, kept: "Edit") -> bool:
        """An edit kept earlier already covers this ground. A LOOK never blocks, and steps aside when covered."""
        if kept.kind is Kind.LOOK:
            return False
        if self.kind is Kind.LOOK:
            return kept.start <= self.start and self.end <= kept.end
        return self.start < kept.end and kept.start < self.end


Finder = Callable[[Doc], Iterable[Edit]]
Widening = Callable[[Span], Span]


def look(span: Span) -> Edit:
    return Edit(span.start_char, span.end_char, Kind.LOOK)


def keep(span: Span) -> Edit:
    return Edit(span.start_char, span.end_char, Kind.KEEP, span.text)


def replace(span: Span, text: str) -> Edit:
    return Edit(span.start_char, span.end_char, Kind.SAY, text)


def say(span: Span, words: str) -> Edit:
    """Say `words` in place of the span, bent to fit it, so `leverages` becomes `uses`."""
    first, *rest = words.split()
    return replace(span, " ".join([bend(first, span[0]), *rest]))


def bend(word: str, like: Token) -> str:
    """Inflect `word` the way `like` is inflected, keeping its case."""
    if like.lemma_ == word:
        return like.text
    if like.tag_[:2] in ("VB", "NN"):
        word = (getInflection(word, like.tag_) or [word])[0]
    return word[0].upper() + word[1:] if like.is_title else word


def repunctuate(span: Span, text: str) -> Edit:
    """Say `text` in place of a punctuation span and the spaces around it. Ending in a full stop makes it a STOP."""
    doc, last = span.doc, span[-1]
    start = doc[span.start - 1].idx + len(doc[span.start - 1]) if span.start else span.start_char
    end = last.idx + len(last) + len(last.whitespace_)
    return Edit(start, end, Kind.STOP if text.endswith(". ") else Kind.SAY, text)


# A cut takes with it whatever it would leave stranded.
def with_adverbs(span: Span) -> Span:
    """An adverb that only modified what is going, as in `a perfectly real path`."""
    doc, start = span.doc, span.start
    while start > 0 and doc[start - 1].dep_ == "advmod" and start <= doc[start - 1].head.i < span.end:
        start -= 1
    return doc[start : span.end]


def with_stars(span: Span) -> Span:
    """The markdown marks around it, as in `the **real** problem`."""
    doc, start, end = span.doc, span.start, span.end
    while start > 0 and end < len(doc) and doc[start - 1].text == "*" and doc[end].text == "*":
        start, end = start - 1, end + 1
    return doc[start:end]


def with_hyphen(span: Span) -> Span:
    """The hyphen glued to it, as in `genuinely-different`."""
    doc, end = span.doc, span.end
    if end < len(doc) and doc[end].text == "-" and not doc[end - 1].whitespace_:
        end += 1
    return doc[span.start : end]


def with_comma(span: Span) -> Span:
    """The comma it would leave dangling, as in `Honestly, it works`."""
    doc, end = span.doc, span.end
    if end < len(doc) - 1 and doc[end].text in (",", ":") and doc[span.start].text != ",":
        end += 1
    return doc[span.start : end]


def with_full_stop(span: Span) -> Span:
    """The full stop, when nothing else is left of the sentence, as in `Great question.`."""
    doc, sent, end = span.doc, span.sent, span.end
    if span.start == sent.start and end == sent.end - 1 and doc[end].is_punct:
        end += 1
    return doc[span.start : end]


WIDENINGS: tuple[Widening, ...] = (with_adverbs, with_stars, with_hyphen, with_comma, with_full_stop)


def trailing_space(span: Span) -> int:
    """The space after a span goes too, unless a word is glued to its front (`isn't`) or a mark follows."""
    doc = span.doc
    glued = span.start > 0 and doc[span.start - 1].is_alpha and not doc[span.start - 1].whitespace_
    before_mark = span.end < len(doc) and doc[span.end].is_punct
    return 0 if glued or before_mark else len(span[-1].whitespace_)


def cut(span: Span) -> Edit:
    for widen in WIDENINGS:
        span = widen(span)
    return Edit(span.start_char, span.end_char + trailing_space(span), Kind.CUT)
