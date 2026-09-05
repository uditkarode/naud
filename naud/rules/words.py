"""Rules about words: the book's tables, `lives in` and `sits at`, `worth knowing`, what `bites`,
a tail that only insists, a tail that means `only`, and a sentence that opens on a bare `This`."""
from collections.abc import Iterator
from functools import cache

from spacy.matcher import Matcher
from spacy.tokens import Doc, Span, Token

from ..book import Entry, Words
from ..edit import Edit, Finder, Kind, base, bend, cut, keep, look, replace, say
from ..parse import model
from .grammar import as_span, is_subject, subject_of
from .match import Pattern, matching, pattern, spans


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
    """A word is said instead. CUT, LOOK and KEEP do what they say. Half of a hyphenated word (`byte-identical`) is kept.
    A quoted mention, or a predicate to cut (`the data is real`), is only looked at."""
    if entry is Kind.KEEP or compound(span):
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


def compound(span: Span) -> bool:
    """The second half of a hyphenated word, as in `byte-identical`."""
    doc, at = span.doc, span.start
    return at > 1 and doc[at - 1].text == "-" and not doc[at - 2].whitespace_ and not doc[at - 1].whitespace_


# `the risk lives in the gap` → `the risk is in the gap`, and `BT sits at 0ms` → `BT is at 0ms`
VERBS = ("live", "sit")
PLACES = (
    "in", "at", "inside", "within", "on", "between", "behind", "next", "beside", "near", "under", "above", "below", "outside",
    "somewhere", "here", "there",
)
PEOPLE = frozenset({"i", "you", "he", "she", "we", "they", "who", "someone", "everyone", "people"})
PLACE_ENTITIES = frozenset({"GPE", "LOC", "FAC"})


def is_person(t: Token | None) -> bool:
    return t is not None and (t.lower_ in PEOPLE or t.ent_type_ == "PERSON")


def is_place(t: Token | None) -> bool:
    return t is not None and t.ent_type_ in PLACE_ENTITIES


def form_of_be(verb: Token, who: Token | None) -> str:
    plural = who is not None and (who.tag_ in ("NNS", "NNPS") or who.lower_ in ("we", "they", "you"))
    return {"VBZ": "is", "VBP": "are", "VBD": "were" if plural else "was", "VBN": "been"}.get(verb.tag_, "be")


def unplace(span: Span) -> Edit:
    """Someone or somewhere is meant, or no one is (`Sit here.`), so only look. Anything else `is in` where it said `lives in`."""
    verb, where = span[0], span[-1]
    who = subject_of(verb)
    place = next((c for c in where.children if c.dep_ == "pobj"), None)
    if who is None or is_person(who) or is_place(place):
        return look(span)
    return replace(span, f"{form_of_be(verb, who)} {where.lower_}")


lives = matching(lambda: [pattern(f"{verb} {place}", "VERB") for verb in VERBS for place in PLACES], unplace)


# `Worth knowing: X` → `X`, `one thing worth flagging: X` → `one thing: X`, and `both are worth fixing` → `both need fixing`.
NOTES = ("knowing", "noting", "flagging", "saying", "stating", "mentioning", "a mention", "a glance", "your call")
FRAME_LEAD = frozenset({"ADV", "CCONJ", "PUNCT"})
COLON_REACH = 5  # tokens of frame (`worth knowing before you deploy:`) to look through for the colon


def unframe(span: Span) -> Edit:
    """A frame announces what follows a colon, so the frame goes. Opening its sentence it takes the colon
    with it, so the fact stands alone. In the middle of one the colon stays and only the frame goes.
    Without a colon nothing is being announced (`worth a glance before you trust it`), so it is only looked at."""
    doc, sent = span.doc, span.sent
    colon = next((t.i for t in doc[span.end : min(span.end + COLON_REACH, len(doc))] if t.text == ":"), None)
    if colon is None:
        return look(span)
    if any(t.pos_ not in FRAME_LEAD for t in doc[sent.start : span.start]):
        before = doc[span.start - 1]
        return Edit(before.idx + len(before), span.end_char, Kind.CUT)
    return cut(doc[sent.start : colon + 1])


def is_negation(word: Token) -> bool:
    return word.lemma_ in ("not", "never") or word.text == "n\u0027t"


def preceding(span: Span) -> Token | None:
    """The word in front of the span, past any adverb, as in `is genuinely worth fixing`."""
    doc, at = span.doc, span.start
    while at > 0 and doc[at - 1].pos_ == "ADV" and not is_negation(doc[at - 1]):
        at -= 1
    return doc[at - 1] if at else None


def leans_back(span: Span) -> bool:
    """`tests worth keeping` leans on the words in front of it, where `; worth deleting` stands on its own."""
    word = preceding(span)
    return word is not None and (word.is_alpha or word.like_num or word.text == ",")


def unworth(span: Span) -> Edit:
    """`X is worth fixing` → `X needs fixing`, `tests worth keeping` → `tests to keep`, `worth deleting` →
    `needs deleting`, and a frame is unframed. After a `be` a frame is the sentence's own predicate
    (`whether it's worth a mention`), so it is only looked at."""
    doc, after = span.doc, span[1:]
    before = preceding(span)
    gerund = after[0].tag_ == "VBG"
    if before is not None and is_negation(before):
        return look(span)
    if before is not None and before.lemma_ == "be":
        if not gerund:
            return look(span)
        glued = before.idx > 0 and not doc.text[before.idx - 1].isspace()
        return replace(doc[before.i : span.end], f"{' ' if glued else ''}{bend('need', before)} {after.text}")
    if after.text.lower() in NOTES:
        return unframe(span)
    if not gerund:
        return look(span)
    if leans_back(span):
        return replace(span, f"to {base(after[0])}")
    return replace(span, f"{'Needs' if span[0].is_title else 'needs'} {after.text}")


def worth_patterns() -> list[Pattern]:
    return [[{"LOWER": "worth"}, {"TAG": "VBG"}], *(pattern(f"worth {note}") for note in NOTES)]


worth = matching(worth_patterns, unworth)


# `the cap will bite again` → `the cap will cause a problem again`. What it bites is meant when there is an object,
# as in `only bites a recovered process`, and that is only looked at.
def unbite(span: Span) -> Edit:
    if any(child.dep_ == "dobj" for child in span.root.children):
        return look(span)
    return say(span, "cause a problem")  # a noun-tagged `bites` bends `cause` to `causes` too, the -s being one form


# The tagger reads `bites` as a plural noun whenever its subject is a noun or a pointer word, and hangs the
# subject off it as a modifier, so `the cap bites` parses as one noun phrase. A noun-tagged `bites` is the verb
# where it has a subject of its own: a noun read as a compound after a determiner, a pointer word no plural
# follows, or a plain subject. Joined by `and` to a verb it is a verb too.
POINTERS = frozenset({"this", "that", "what", "which"})


def is_bite(t: Token) -> bool:
    if t.pos_ == "VERB":
        return True
    if t.tag_ != "NNS":
        return False
    if t.dep_ == "conj":
        return t.head.pos_ == "VERB"
    det = next((c for c in t.children if c.dep_ == "det"), None)
    if det is not None and (det.lower_ in POINTERS or any(c.dep_ == "compound" for c in t.children)):
        return True
    return subject_of(t) is not None


bite_spans = spans(lambda: [[{"LEMMA": "bite"}]])


def bites(doc: Doc) -> Iterator[Edit]:
    for span in bite_spans(doc):
        if is_bite(span[0]):
            yield unbite(span)


# `the failures are rare, and they're real` → the tail only insists, so it goes. Where `real` describes a noun
# (`and they're real problems`) it is doing a job, so the pattern passes it over.
REAL_TAIL: Pattern = [{"LOWER": "and"}, {"LOWER": "they"}, {"LEMMA": "be"}, {"LOWER": "real", "DEP": "acomp"}]

insists = matching(lambda: [REAL_TAIL], cut)


# `it touches the parser and nothing else` → `it touches the parser only`. The tail has to hang off what
# came before it and close the clause there. Where it has a verb of its own (`and nothing else may touch it`),
# or carries a phrase (`and nothing else at all`), `only` cannot stand in its place, so it is left alone.
NOTHING_ELSE: Pattern = [{"LOWER": "and"}, {"LOWER": "nothing"}, {"LOWER": "else"}]
nothing_else = spans(lambda: [NOTHING_ELSE])


def narrows(doc: Doc) -> Iterator[Edit]:
    for span in nothing_else(doc):
        if span[1].dep_ == "conj" and (span.end == len(doc) or doc[span.end].is_punct):
            yield replace(span, "only")


# A sentence that opens on a bare `This` points at something only the writer can see.
# Canonical English: `If a pronoun would be ambiguous among antecedents, repeat the noun.`
DEMONSTRATIVES = ("this", "that", "these", "those")


def vague(doc: Doc) -> Iterator[Edit]:
    for sent in doc.sents:
        first = sent[0]
        if first.lower_ in DEMONSTRATIVES and first.pos_ == "PRON" and is_subject(first):
            yield look(as_span(first))
