"""What the parse says, in words the rules can use."""
from collections.abc import Iterator, Sequence
from typing import TypeVar

from spacy.tokens import Span, Token

T = TypeVar("T")

SUBJECT = frozenset({"nsubj", "nsubjpass", "csubj", "expl"})
DASHES = ("—", "–")


def is_subject(t: Token) -> bool:
    return t.dep_ in SUBJECT


def subject_of(head: Token) -> Token | None:
    return next((c for c in head.children if is_subject(c)), None)


def negated(t: Token) -> bool:
    return any(c.dep_ == "neg" for c in t.children)


def has_aux(t: Token) -> bool:
    return any(c.dep_ in ("aux", "auxpass") for c in t.children)


def as_span(t: Token) -> Span:
    return t.doc[t.i : t.i + 1]


def pairs(items: Sequence[T]) -> Iterator[tuple[T, T]]:
    return zip(items, items[1:])
