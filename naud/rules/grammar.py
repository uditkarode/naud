"""What the parse says, in words the rules can use."""
from collections.abc import Iterator, Sequence
from typing import TypeVar

from spacy.tokens import Span, Token

T = TypeVar("T")

SUBJECT = frozenset({"nsubj", "nsubjpass", "csubj", "expl"})
DASHES = ("—", "–")
POINTERS = frozenset({"this", "that", "what", "which"})


def is_subject(t: Token) -> bool:
    return t.dep_ in SUBJECT


def subject_of(head: Token) -> Token | None:
    return next((c for c in head.children if is_subject(c)), None)


# The tagger reads a verb whose subject is a noun or a pointer word as a plural noun instead, and hangs the
# subject off it as a modifier, so `the cap bites` and `the ordering matters` each parse as one noun phrase.
def is_verb(t: Token) -> bool:
    """The word is the verb here, whatever the tagger called it: it has a subject of its own, it is a noun read
    as a compound after a determiner, or it is a pointer word no plural follows. Joined by `and` to a verb it is
    a verb too."""
    if t.pos_ == "VERB" or subject_of(t) is not None:
        return True
    if t.tag_ != "NNS":
        return False
    if t.dep_ == "conj":
        return t.head.pos_ == "VERB"
    det = next((c for c in t.children if c.dep_ == "det"), None)
    return det is not None and (det.lower_ in POINTERS or any(c.dep_ == "compound" for c in t.children))


def negated(t: Token) -> bool:
    return any(c.dep_ == "neg" for c in t.children)


def has_aux(t: Token) -> bool:
    return any(c.dep_ in ("aux", "auxpass") for c in t.children)


def as_span(t: Token) -> Span:
    return t.doc[t.i : t.i + 1]


def pairs(items: Sequence[T]) -> Iterator[tuple[T, T]]:
    return zip(items, items[1:])
