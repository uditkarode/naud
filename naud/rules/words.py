"""Rules about words: the book's tables, `lives in`, and a sentence that opens on a bare `This`."""
from collections.abc import Iterator
from functools import cache

from spacy.matcher import Matcher
from spacy.tokens import Doc, Span, Token

from ..book import Entry, Words
from ..edit import Edit, Finder, Kind, cut, keep, look, replace, say
from ..parse import model
from .grammar import as_span, is_subject, subject_of
from .match import matching, pattern


def table(entries: Words, pos: str | None = None) -> Finder:
    """A finder for a table of phrases. Each match is decided by its entry."""

    @cache
    def matcher() -> Matcher:
        built = Matcher(model().vocab)
        for phrase in entries:
            built.add(phrase, [pattern(phrase, pos)])
        return built

    def find(doc: Doc) -> Iterator[Edit]:
        for key, start, end in matcher()(doc):
            yield decide(doc[start:end], entries[model().vocab.strings[key]])

    return find


def decide(span: Span, entry: Entry) -> Edit:
    """A word is said instead. CUT, LOOK and KEEP do what they say. A quoted mention, or a predicate to cut (`the data is real`), is only looked at."""
    if entry is Kind.KEEP:
        return keep(span)
    if quoted(span) or (entry is Kind.CUT and span.root.dep_ == "acomp"):
        return look(span)
    if entry is Kind.LOOK:
        return look(span)
    if entry is Kind.CUT:
        return cut(span)
    return say(span, entry)


def quoted(span: Span) -> bool:
    doc = span.doc
    return span.start > 0 and span.end < len(doc) and doc[span.start - 1].is_quote and doc[span.end].is_quote


# `the risk lives in the gap` → `the risk is in the gap`
PLACES = ("in", "at", "inside", "within", "on", "somewhere", "here", "there")
PEOPLE = frozenset({"i", "you", "he", "she", "we", "they", "who", "someone", "everyone", "people"})
PLACE_ENTITIES = frozenset({"GPE", "LOC", "FAC"})


def is_person(t: Token | None) -> bool:
    return t is not None and (t.lower_ in PEOPLE or t.ent_type_ == "PERSON")


def is_place(t: Token | None) -> bool:
    return t is not None and t.ent_type_ in PLACE_ENTITIES


def form_of_be(verb: Token, who: Token | None) -> str:
    plural = who is not None and (who.tag_ in ("NNS", "NNPS") or who.lower_ in ("we", "they", "you"))
    return {"VBZ": "is", "VBP": "are", "VBD": "were" if plural else "was"}.get(verb.tag_, "be")


def unplace(span: Span) -> Edit:
    """Someone or somewhere is meant, so only look. Anything else `is in` where it said `lives in`."""
    verb, where = span[0], span[-1]
    who = subject_of(verb)
    place = next((c for c in where.children if c.dep_ == "pobj"), None)
    if is_person(who) or is_place(place):
        return look(span)
    return replace(span, f"{form_of_be(verb, who)} {where.lower_}")


lives = matching(lambda: [pattern(f"live {place}", "VERB") for place in PLACES], unplace)


# A sentence that opens on a bare `This` points at something only the writer can see.
# Canonical English: `If a pronoun would be ambiguous among antecedents, repeat the noun.`
DEMONSTRATIVES = ("this", "that", "these", "those")


def vague(doc: Doc) -> Iterator[Edit]:
    for sent in doc.sents:
        first = sent[0]
        if first.lower_ in DEMONSTRATIVES and first.pos_ == "PRON" and is_subject(first):
            yield look(as_span(first))
