"""Rules about how much: sentences over WORDS words, paragraphs over SENTENCES sentences."""
from collections.abc import Iterator
from math import ceil

from spacy.tokens import Doc, Span, Token

from .. import book
from ..edit import Edit, Kind, look, repunctuate
from .grammar import has_aux, subject_of

JOINERS = {"and": ". ", "but": ". But ", "so": ". So ", "yet": ". Yet "}  # `or` is left alone


def too_long(sent: Span) -> bool:
    return sum(not t.is_punct for t in sent) > book.WORDS


def own_verb(verb: Token) -> bool:
    """Has its own modal, or none to share (`can reconcile and each create` shares one)."""
    return has_aux(verb) or (verb.tag_ != "VB" and not has_aux(verb.head))


def second_clause(verb: Token) -> bool:
    return verb.dep_ == "conj" and own_verb(verb) and subject_of(verb) is not None


def in_parenthesis(before: Span) -> bool:
    return before.text.count("(") > before.text.count(")")


def joins(sent: Span) -> Iterator[tuple[Span, str]]:
    """Where a second clause begins: the `, and` before it, and what to say there instead."""
    doc = sent.doc
    for verb in sent:
        if not second_clause(verb):
            continue
        first = verb.left_edge.i
        cc = doc[first - 1] if first and doc[first - 1].dep_ == "cc" else None
        start = cc.i if cc is not None else first
        if start and doc[start - 1].text == ",":
            start -= 1
        if start == first or in_parenthesis(doc[sent.start : start]):
            continue
        if cc is None:
            yield doc[start:first], ". "
        elif cc.lower_ in JOINERS:
            yield doc[start:first], JOINERS[cc.lower_]


def split(doc: Doc) -> Iterator[Edit]:
    """A sentence over the limit breaks where two clauses meet: `X, and Y` → `X. Y`."""
    for sent in doc.sents:
        if too_long(sent):
            for span, text in joins(sent):
                yield repunctuate(span, text)


def long(doc: Doc) -> Iterator[Edit]:
    """A sentence over the limit with nowhere to break is only looked at."""
    for sent in doc.sents:
        if too_long(sent) and next(joins(sent), None) is None:
            yield look(sent)


def paragraphs(doc: Doc) -> Iterator[Edit]:
    """A paragraph over the limit breaks into even parts."""
    sents = list(doc.sents)
    if len(sents) <= book.SENTENCES:
        return
    size = ceil(len(sents) / ceil(len(sents) / book.SENTENCES))
    for last, first in zip(sents[size - 1 :: size], sents[size::size]):
        yield Edit(last.end_char, first.start_char, Kind.SAY, "\n\n")
