"""Rules about the marks that glue two clauses into one sentence: dashes, colons, semicolons."""
from collections.abc import Iterator

from spacy.tokens import Doc, Span, Token

from ..edit import Edit, repunctuate
from .grammar import DASHES, as_span, is_subject

RELATIVES = frozenset({"which", "who", "whom", "whose", "where"})
SUBORDINATORS = frozenset({"before", "after", "if", "when", "because", "while", "although", "since", "unless", "once", "as", "until", "whenever", "though", "even"})


def stands(before: Span) -> bool:
    """Can end with a full stop. Neither a subordinate clause (`before you do`) nor a bare noun phrase (`The difference`)."""
    words = [t for t in before if t.dep_ != "cc"]
    if not words or words[0].lower_ in SUBORDINATORS:
        return False
    return any(t.pos_ in ("VERB", "AUX") for t in before) or before.root.pos_ not in ("NOUN", "PROPN")


def opens_clause(after: Span) -> bool:
    """Opens a clause: an imperative, or a subject hanging off a verb above the first word, before any mark."""
    if not after or after[0].lower_ in RELATIVES | SUBORDINATORS:
        return False
    if after[0].dep_ == "cc" and len(after) > 1:
        after = after[1:]
    first = after[0]
    if first.tag_ == "VB" and first.pos_ == "VERB":
        return True
    above = (first, *first.ancestors)
    for t in after:
        if t.is_punct:
            return False
        if is_subject(t) and t.head in above:
            return True
    return False


def breaks(mark: Token) -> bool:
    """Both sides of the mark can stand alone."""
    doc, sent = mark.doc, mark.sent
    return stands(doc[sent.start : mark.i]) and opens_clause(doc[mark.i + 1 : sent.end])


def between_numbers(mark: Token) -> bool:
    doc = mark.doc
    return 0 < mark.i < len(doc) - 1 and doc[mark.i - 1].like_num and doc[mark.i + 1].like_num


def dashes(doc: Doc) -> Iterator[Edit]:
    """`X — Y` → `X. Y` when both sides stand alone, else `X, Y`. A pair of dashes is a parenthesis, so commas."""
    for sent in doc.sents:
        marks = [t for t in sent if t.text in DASHES and not between_numbers(t)]
        for mark in marks:
            alone = len(marks) == 1 and breaks(mark)
            yield repunctuate(as_span(mark), ". " if alone else ", ")


def colons(doc: Doc) -> Iterator[Edit]:
    """`X: Y` and `X; Y` → `X. Y` when both sides stand alone."""
    for sent in doc.sents:
        for mark in sent:
            if mark.text in (":", ";") and mark.whitespace_ and breaks(mark):
                yield repunctuate(as_span(mark), ". ")
