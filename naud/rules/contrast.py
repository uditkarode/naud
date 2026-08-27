"""Rules about saying what something is not: `not X but Y`, `A rather than B`, `No X. No Y. Just Z.`."""
from collections.abc import Iterator
from itertools import takewhile

from spacy.tokens import Doc, Span, Token

from ..edit import Edit, cut, look
from .grammar import DASHES, SUBJECT, is_subject, negated, pairs, subject_of
from .match import Pattern, matching, pattern, spans

# `not just X, but Y` and `not just X, it's Y` → `Y`
MARKERS = ("just", "only", "simply", "merely")
NOT = {"LEMMA": "not"}
MARKER = {"LOWER": {"IN": list(MARKERS)}, "OP": "?"}
X = {"POS": {"NOT_IN": ["VERB", "AUX"]}, "IS_PUNCT": False, "OP": "{1,8}"}
CLEFT: list[Pattern] = [
    [NOT, MARKER, X, {"ORTH": ",", "OP": "?"}, {"LOWER": "but"}, {"LOWER": {"IN": ["also", "rather"]}, "OP": "?"}],
    [NOT, MARKER, X, {"ORTH": ","}, {"LOWER": {"IN": ["it", "this", "that"]}}, {"LEMMA": "be"}, {"LOWER": "also", "OP": "?"}],
]


def uncleft(span: Span) -> Edit:
    """`not just about A, but about B` → `about B`. Y has to mirror X. If it opens a clause of its own, it is only looked at."""
    doc = span.doc
    if span.end == len(doc):
        return look(span)
    y = doc[span.end]
    if is_subject(y) or is_subject(y.head):
        return look(span)
    mirrored = span[1].lower_ in MARKERS or y.lower_ == span[1].lower_
    return cut(span) if mirrored else look(span)


cleft = matching(lambda: CLEFT, uncleft)


# `A rather than B` → `A`
CONNECTORS = ("rather than", "instead of", "as opposed to", "and not", ", not")
CLAUSE_END = frozenset({",", ".", ";", ":", ")", "!", "?", *DASHES})


def phrase_after(span: Span) -> Span:
    """The span plus the phrase hanging off its end, as far as the parse allows, minus any trailing mark."""
    doc = span.doc
    if span.end == len(doc):
        return span
    first = doc[span.end]

    def hangs_off(t: Token) -> bool:
        return t.left_edge.i >= span.start and t.dep_ != "ROOT" and subject_of(t) is None

    end = max((t.right_edge.i + 1 for t in takewhile(hangs_off, (first, *first.ancestors))), default=span.end)
    while end > span.end and doc[end - 1].is_punct:
        end -= 1
    return doc[span.start : end]


def has_names(b: Span) -> bool:
    """A number or a name is what a `rather than` is there to say."""
    return any(t.text[0].isdigit() or t.pos_ == "PROPN" for t in b)


def untail(span: Span) -> Edit:
    """`A rather than B` → `A`, when B is plain and ends the clause. Otherwise only look."""
    doc, phrase = span.doc, phrase_after(span)
    b = phrase[len(span) :]
    ends_clause = phrase.end == len(doc) or doc[phrase.end].text in CLAUSE_END
    participle = span[-1].lower_ == "not" and len(b) > 0 and b[0].tag_ == "VBG"
    if not b or has_names(b) or participle or not ends_clause:
        return look(span)
    return cut(phrase)


tail = matching(lambda: [pattern(connector) for connector in CONNECTORS], untail)


# `No X. No Y. Just Z.` → `Z.`
NO_X: Pattern = [{"LOWER": "no"}, {"POS": {"NOT_IN": ["VERB", "AUX"]}, "IS_PUNCT": False, "OP": "{1,5}"}, {"ORTH": {"IN": [",", "."]}}]
no_x = spans(lambda: [NO_X])


def runs(pieces: dict[int, int]) -> Iterator[tuple[int, int]]:
    """Chains of pieces where one ends where the next starts, as (start, end)."""
    for start in pieces:
        if start not in pieces.values():
            end = start
            while end in pieces:
                end = pieces[end]
            yield start, end


def staccato(doc: Doc) -> Iterator[Edit]:
    pieces = {piece.start: piece.end for piece in no_x(doc)}
    for start, end in runs(pieces):
        if end < len(doc) and doc[end].lower_ == "just":
            yield cut(doc[start : end + 1])


# `It's not X. It's Y.` → `It's Y.`
def is_copula(sent: Span) -> bool:
    return sent.root.lemma_ == "be"


def one_clause(sent: Span) -> bool:
    return sum(t.pos_ in ("VERB", "AUX") and t.dep_ != "aux" for t in sent) == 1


def subject_name(sent: Span) -> str | None:
    """The subject's lemma, with `it`, `this` and `that` as one and the same."""
    s = subject_of(sent.root)
    if s is None:
        return None
    return "it" if s.lower_ in ("it", "this", "that") else s.lemma_


def same_subject(a: Span, b: Span) -> bool:
    return subject_name(a) is not None and subject_name(a) == subject_name(b)


def not_but(doc: Doc) -> Iterator[Edit]:
    for a, b in pairs(list(doc.sents)):
        if is_copula(a) and negated(a.root) and one_clause(a) and is_copula(b) and not negated(b.root) and same_subject(a, b):
            yield cut(a)


# `Not that X is Y. It isn't.` → gone
def opens_not_that(sent: Span) -> bool:
    return len(sent) > 1 and sent[0].lower_ == "not" and sent[1].lower_ == "that"


def short_denial(sent: Span) -> bool:
    return len(sent) <= 4 and negated(sent.root)


def not_that(doc: Doc) -> Iterator[Edit]:
    for a, b in pairs(list(doc.sents)):
        if opens_not_that(a) and short_denial(b):
            yield cut(doc[a.start : b.end])
