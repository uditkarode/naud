"""The rules. Each is a function from a parsed line to the edits it wants, in order of who wins overlaps."""
from collections.abc import Callable, Iterable, Iterator
from math import ceil
from typing import Any

from spacy.matcher import Matcher
from spacy.tokens import Doc, Span, Token

from . import book
from .core import Edit, nlp
from .cuts import SUBJECT, cut, flag, glue, reach, swap

Rule = Callable[[Doc], Iterable[Edit]]
Fix = Callable[[Span], Edit | None]
Pattern = list[dict[str, Any]]

MARKERS: list[str] = ["just", "only", "simply", "merely"]
PERSON: frozenset[str] = frozenset({"i", "you", "he", "she", "we", "they", "who", "someone", "everyone", "people"})
PLACE: frozenset[str] = frozenset({"GPE", "LOC", "FAC"})
DASHES: tuple[str, ...] = ("—", "–")
END: frozenset[str] = frozenset({",", ".", ";", ":", ")", "!", "?", *DASHES})
RELATIVE: frozenset[str] = frozenset({"which", "who", "whom", "whose", "where"})
SUB: frozenset[str] = frozenset({"before", "after", "if", "when", "because", "while", "although", "since", "unless", "once", "as", "until", "whenever", "though", "even"})


def pattern(phrase: str, pos: str | None = None) -> Pattern:
    """Match a phrase by its first word's lemma ("live in" finds "lives in") and the rest as written."""
    first, *rest = nlp(phrase)
    return [{"LEMMA": first.lemma_, **({"POS": pos} if pos else {})}, *({"LOWER": t.lower_} for t in rest)]


def matching(name: str, patterns: list[Pattern], fix: Fix) -> Rule:
    """A rule that hands every match of the patterns to `fix`."""
    matcher = Matcher(nlp.vocab)
    matcher.add(name, patterns)

    def rule(doc: Doc) -> Iterator[Edit]:
        return filter(None, (fix(doc[s:e]) for _, s, e in matcher(doc)))

    return rule


def say(span: Span, new: str | None, name: str) -> Edit:
    """"" cuts, None points, anything else is said instead. A predicate ("the data is real") or a quoted mention is only pointed at."""
    doc = span.doc
    quoted = span.start > 0 and span.end < len(doc) and doc[span.start - 1].is_quote and doc[span.end].is_quote
    if new is None or quoted or (new == "" and span.root.dep_ == "acomp"):
        return flag(span, name)
    return cut(span, name) if new == "" else swap(span, new, name)


def table(name: str, entries: book.Words, pos: str | None = None) -> Rule:
    """A rule from a phrase table (see book.py for what the values mean)."""
    matcher = Matcher(nlp.vocab)
    for phrase in entries:
        matcher.add(phrase, [pattern(phrase, pos)])

    def rule(doc: Doc) -> Iterator[Edit]:
        for key, s, e in matcher(doc):
            span, phrase = doc[s:e], nlp.vocab.strings[key]
            yield say(span, span.text if entries[phrase] == phrase else entries[phrase], name)

    return rule


# "not just X, but Y" / "not just X, it's Y" → "Y"
X: dict[str, Any] = {"POS": {"NOT_IN": ["VERB", "AUX"]}, "IS_PUNCT": False, "OP": "{1,8}"}
CLEFT: list[Pattern] = [
    [{"LEMMA": "not"}, {"LOWER": {"IN": MARKERS}, "OP": "?"}, X, {"ORTH": ",", "OP": "?"}, {"LOWER": "but"}, {"LOWER": {"IN": ["also", "rather"]}, "OP": "?"}],
    [{"LEMMA": "not"}, {"LOWER": {"IN": MARKERS}, "OP": "?"}, X, {"ORTH": ","}, {"LOWER": {"IN": ["it", "this", "that"]}}, {"LEMMA": "be"}, {"LOWER": "also", "OP": "?"}],
]


def uncleft(span: Span) -> Edit:
    """Cut when Y mirrors X ("not just about A, but about B"). Otherwise only point at it."""
    doc = span.doc
    after = doc[span.end] if span.end < len(doc) else None
    mirrored = span[1].lower_ in MARKERS or (after is not None and after.lower_ == span[1].lower_)
    opens = after is None or after.dep_ in SUBJECT or after.head.dep_ in SUBJECT
    return flag(span, "cleft") if opens or not mirrored else cut(span, "cleft")


# "A rather than B" → "A"
TAIL: list[Pattern] = [pattern(p) for p in ("rather than", "instead of", "as opposed to", "and not", ", not")]


def plain(tail: Span) -> bool:
    """No names or numbers: the kind of phrase that can go."""
    return len(tail) > 0 and not any(t.text[0].isdigit() or t.pos_ == "PROPN" for t in tail)


def untail(span: Span) -> Edit:
    """Cut the connector and the phrase after it, when the phrase is plain and ends the clause. Otherwise point."""
    doc, phrase = span.doc, reach(span)
    tail, after = phrase[len(span) :], doc[phrase.end : phrase.end + 1]
    ends = not after or after[0].text in END
    clause = span[-1].lower_ == "not" and len(tail) > 0 and tail[0].tag_ == "VBG"
    return cut(phrase, "tail") if plain(tail) and ends and not clause else flag(span, "tail")


# "the risk lives in the gap" → "the risk is in the gap"
LIVES: list[Pattern] = [pattern(f"live {p}", "VERB") for p in ("in", "at", "inside", "within", "on", "somewhere", "here", "there")]


def unplace(span: Span) -> Edit:
    """When someone or somewhere is meant, only point at it."""
    verb, prep = span[0], span[-1]
    who = next((c for c in verb.children if c.dep_ in SUBJECT), None)
    where = next((c for c in prep.children if c.dep_ == "pobj"), None)
    if (who is not None and (who.lower_ in PERSON or who.ent_type_ == "PERSON")) or (where is not None and where.ent_type_ in PLACE):
        return flag(span, "lives")
    plural = who is not None and (who.tag_ in ("NNS", "NNPS") or who.lower_ in ("we", "they", "you"))
    be = {"VBZ": "is", "VBP": "are", "VBD": "were" if plural else "was"}.get(verb.tag_, "be")
    return Edit(span.start_char, span.end_char, f"{be} {prep.lower_}", "lives")


# "No X. No Y. Just Z." → "Z."
chunks = Matcher(nlp.vocab)
chunks.add("no", [[{"LOWER": "no"}, {"POS": {"NOT_IN": ["VERB", "AUX"]}, "IS_PUNCT": False, "OP": "{1,5}"}, {"ORTH": {"IN": [",", "."]}}]])


def staccato(doc: Doc) -> Iterator[Edit]:
    chunk = {s: e for _, s, e in chunks(doc)}
    for s in (s for s in chunk if s not in chunk.values()):
        e = s
        while e in chunk:
            e = chunk[e]
        if e < len(doc) and doc[e].lower_ == "just":
            yield cut(doc[s : e + 1], "staccato")


# "It's not X. It's Y." → "It's Y."
def negated(t: Token) -> bool:
    return any(c.dep_ == "neg" for c in t.children)


def subject(sent: Span) -> str | None:
    s = next((c for c in sent.root.children if c.dep_ in SUBJECT), None)
    return None if s is None else "it" if s.lower_ in ("it", "this", "that") else s.lemma_


def pairs(doc: Doc) -> Iterator[tuple[Span, Span]]:
    sents = list(doc.sents)
    return zip(sents, sents[1:])


def simple(sent: Span) -> bool:
    """One verb, so the sentence is nothing but the negation."""
    return sum(t.pos_ in ("VERB", "AUX") and t.dep_ != "aux" for t in sent) == 1


def unnegate(doc: Doc) -> Iterator[Edit]:
    for a, b in pairs(doc):
        if a.root.lemma_ == b.root.lemma_ == "be" and negated(a.root) and not negated(b.root) and simple(a) and subject(a) and subject(a) == subject(b):
            yield cut(a, "not-but")


# "Not that X is Y. It isn't." → gone
def unhedge(doc: Doc) -> Iterator[Edit]:
    for a, b in pairs(doc):
        if a[0].lower_ == "not" and len(a) > 1 and a[1].lower_ == "that" and len(b) <= 4 and negated(b.root):
            yield cut(doc[a.start : b.end], "not-that")


# "X — Y", "X: Y", "X; Y" gluing two clauses → "X. Y"
def opens_clause(after: Span) -> bool:
    """The first token starts a clause: an imperative, or a subject (before any punctuation) hanging off a verb above it."""
    if after[0].tag_ == "VB" and after[0].pos_ == "VERB":
        return True
    for x in after:
        if x.is_punct:
            return False
        if x.dep_ in SUBJECT and x.head in (after[0], *after[0].ancestors):
            return True
    return False


def stands(span: Span) -> bool:
    """Can end with a full stop: has a verb, or isn't a bare noun phrase ("Good", "Noted", "Not weird")."""
    return any(t.pos_ in ("VERB", "AUX") for t in span) or span.root.pos_ not in ("NOUN", "PROPN")


def breaks(t: Token) -> bool:
    """Both sides of t can stand alone. The left isn't "before you do" or "The difference". The right opens straight into a clause."""
    doc, sent = t.doc, t.sent
    before, after = doc[sent.start : t.i], doc[t.i + 1 : sent.end]
    body = [x for x in before if x.dep_ != "cc"]
    if not body or body[0].lower_ in SUB or not stands(before) or not after or after[0].lower_ in RELATIVE | SUB:
        return False
    return opens_clause(after[1:] if after[0].dep_ == "cc" and len(after) > 1 else after)


def joints(doc: Doc) -> Iterator[Edit]:
    def one(t: Token) -> Span:
        return doc[t.i : t.i + 1]

    def between_numbers(t: Token) -> bool:
        return 0 < t.i < len(doc) - 1 and doc[t.i - 1].like_num and doc[t.i + 1].like_num

    for sent in doc.sents:
        dashes = [t for t in sent if t.text in DASHES and not between_numbers(t)]
        for t in dashes:
            yield glue(one(t), ". " if len(dashes) == 1 and breaks(t) else ", ", "dash")
        for t in sent:
            if t.text in (":", ";") and t.whitespace_ and breaks(t):
                yield glue(one(t), ". ", "colon")


# A sentence that opens on a bare "This"/"That" points at something only the writer can see.
# Canonical English: "If a pronoun would be ambiguous among antecedents, repeat the noun."
def vague(doc: Doc) -> Iterator[Edit]:
    for sent in doc.sents:
        if sent[0].lower_ in ("this", "that", "these", "those") and sent[0].pos_ == "PRON" and sent[0].dep_ in SUBJECT:
            yield flag(sent[0:1], "vague")


# Over WORDS words, split where two clauses meet ("X, and Y" → "X. Y"). If there is nowhere to split, point at it.
def own_verb(v: Token) -> bool:
    """A second verb with its own modal, or no modal to share ("can reconcile and each create" shares one)."""

    def aux(t: Token) -> bool:
        return any(c.dep_ in ("aux", "auxpass") for c in t.children)

    return aux(v) or (v.tag_ != "VB" and not aux(v.head))


def joins(sent: Span) -> Iterator[tuple[Span, str]]:
    """(span, text) for each ", and" / ", but" / "," that joins a second clause with its own subject."""
    doc = sent.doc
    for v in sent:
        if v.dep_ == "conj" and own_verb(v) and any(c.dep_ in SUBJECT for c in v.children):
            first = v.left_edge.i
            cc = doc[first - 1] if first and doc[first - 1].dep_ == "cc" else None
            start = cc.i if cc is not None else first
            start -= start > 0 and doc[start - 1].text == ","
            before = doc[sent.start : start].text
            if start < first and before.count("(") <= before.count(")") and (cc is None or cc.lower_ in ("and", "but", "so", "yet")):
                yield doc[start:first], ". " if cc is None or cc.lower_ == "and" else f". {cc.text.capitalize()} "


def split(doc: Doc) -> Iterator[Edit]:
    for sent in doc.sents:
        if sum(not t.is_punct for t in sent) > book.WORDS:
            found = [glue(span, text, "split") for span, text in joins(sent)]
            yield from found or [flag(sent, "long")]


# Over SENTENCES sentences, break the paragraph into even parts.
def paragraphs(doc: Doc) -> Iterator[Edit]:
    sents = list(doc.sents)
    size = ceil(len(sents) / ceil(len(sents) / book.SENTENCES))
    if len(sents) > book.SENTENCES:
        for a, b in zip(sents[size - 1 :: size], sents[size::size]):
            yield Edit(a.end_char, b.start_char, "\n\n", "paragraph")


RULES: list[Rule] = [
    matching("cleft", CLEFT, uncleft),
    matching("tail", TAIL, untail),
    staccato,
    unnegate,
    unhedge,
    table("filler", book.FILLER),
    table("emphasis", book.EMPHASIS),
    table("jargon", book.VERBS, pos="VERB"),
    table("plain", book.PLAIN),
    matching("lives", LIVES, unplace),
    table("look", book.LOOK),
    vague,
    joints,
    split,
    paragraphs,
]
