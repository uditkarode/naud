"""Rules about words: the book's tables, pleasantries said as a sentence of their own, `lives in` and `sits at`,
`serves as` and `boasts`, `worth knowing`, what `bites`, what `matters`, a tail that only insists, a tail that means
`only`, and a sentence that opens on a bare `This`."""
from collections.abc import Iterable, Iterator
from functools import cache

from spacy.matcher import Matcher
from spacy.tokens import Doc, Span, Token

from ..book import Entry, Words
from ..edit import Edit, Finder, Kind, base, bend, cut, keep, look, replace, say
from ..parse import model
from .grammar import as_span, is_subject, is_verb, subject_of
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


def alone(phrases: Iterable[str]) -> Finder:
    """A finder for phrases that say nothing as a sentence of their own (`I hope this helps!`), or opening one before
    a comma (`Of course, it works`). Anywhere else they carry the sentence, as in `let me know if you have any
    questions about the plan`, so they are left alone."""
    find = spans(lambda: [pattern(phrase) for phrase in phrases])

    def rule(doc: Doc) -> Iterator[Edit]:
        for span in find(doc):
            rest = doc[span.end : span.sent.end]
            if span.start == span.sent.start and (all(t.is_punct for t in rest) or rest[0].text == ","):
                yield cut(span)

    return rule


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


def is_plural(who: Token | None) -> bool:
    return who is not None and (
        who.tag_ in ("NNS", "NNPS") or who.lower_ in ("we", "they", "you", "these", "those") or any(c.dep_ == "conj" for c in who.children)
    )


def form_of_be(verb: Token, who: Token | None) -> str:
    """The `be` that takes the verb's place and agrees with `who`: `I am`, `it was`, `they were`."""
    if who is not None and who.lower_ == "i" and verb.tag_ in ("VBP", "VBD"):
        return "am" if verb.tag_ == "VBP" else "was"
    return {"VBZ": "is", "VBP": "are", "VBD": "were" if is_plural(who) else "was", "VBN": "been", "VBG": "being"}.get(verb.tag_, "be")


def unplace(span: Span) -> Edit:
    """Someone or somewhere is meant, or no one is (`Sit here.`), so only look. Anything else `is in` where it said `lives in`."""
    verb, where = span[0], span[-1]
    who = subject_of(verb)
    place = next((c for c in where.children if c.dep_ == "pobj"), None)
    if who is None or is_person(who) or is_place(place):
        return look(span)
    return replace(span, f"{form_of_be(verb, who)} {where.lower_}")


lives = matching(lambda: [pattern(f"{verb} {place}", "VERB") for verb in VERBS for place in PLACES], unplace)


# `Gallery 825 serves as the exhibition space` → `Gallery 825 is the exhibition space`, and `stands as` goes the same
# way. `as` has to be a preposition with a noun of its own, so `serves as many as 200 people`, `stands as of today`
# and `stands as it did` are left alone, and so is the passive `is served as HTML`. The tagger can call a noun a verb,
# as in `the stands as a whole were full`, and a verb in the present or past is never the subject, so that goes too.
SERVE: Pattern = [{"LEMMA": {"IN": ["serve", "stand"]}}, {"LOWER": "as"}]
NOUNS = frozenset({"NOUN", "PROPN", "PRON", "NUM"})
FINITE = frozenset({"VBZ", "VBP", "VBD"})
serve_spans = spans(lambda: [SERVE])


def doer(verb: Token) -> Token | None:
    """The subject, found through the verb `and` joins this one to, or the noun a `that` or `which` stands for."""
    while subject_of(verb) is None and verb.dep_ == "conj":
        verb = verb.head
    who = subject_of(verb)
    if who is not None and who.lower_ in ("that", "which", "who") and verb.dep_ == "relcl":
        return verb.head
    return who


def unserve(span: Span) -> Edit:
    """`was` or `were` turns on who served, so a `served` with no subject in sight is only looked at."""
    verb = span[0]
    who = doer(verb)
    if verb.tag_ == "VBD" and who is None:
        return look(span)
    be = form_of_be(verb, who)
    return replace(span, be.capitalize() if verb.is_title else be)


def serves(doc: Doc) -> Iterator[Edit]:
    for span in serve_spans(doc):
        verb, prep = span[0], span[1]
        noun = any(c.dep_ == "pobj" and c.pos_ in NOUNS for c in prep.children)
        passive = any(c.dep_ == "auxpass" for c in verb.children)
        a_noun = verb.tag_ in FINITE and is_subject(verb)
        if is_verb(verb) and not a_noun and prep.dep_ == "prep" and prep.head.i == verb.i and noun and not passive:
            yield unserve(span)


# `The mall boasts a food court` → `The mall has a food court`. With nothing boasted of directly, as in `boasts about
# his car` or `boasted that he won`, bragging is meant, so that is left alone.
boast_spans = spans(lambda: [[{"LEMMA": "boast"}]])


def boasts(doc: Doc) -> Iterator[Edit]:
    for span in boast_spans(doc):
        word = span[0]
        if is_verb(word) and any(c.dep_ == "dobj" and c.pos_ != "SCONJ" for c in word.children):
            yield say(span, "have")


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


bite_spans = spans(lambda: [[{"LEMMA": "bite"}]])


def bites(doc: Doc) -> Iterator[Edit]:
    for span in bite_spans(doc):
        if is_verb(span[0]):
            yield unbite(span)


# `The split matters: it keeps the offsets simple.` → the frame only calls what follows important, so it goes
# with its colon and the fact stands alone. Someone is meant in `You matter`, so that is left alone. Without a
# colon nothing is announced, and past the front of a sentence the colon keeps a left half of its own
# (`One reason this matters: X`), so both are only looked at.
def unmatter(span: Span) -> Edit:
    doc, sent = span.doc, span.sent
    colon = next((t.i for t in doc[span.end : min(span.end + COLON_REACH, sent.end)] if t.text == ":"), None)
    if colon is None or span.start != sent.start:
        return look(span)
    return cut(doc[sent.start : colon + 1])


matter_spans = spans(lambda: [[{"LEMMA": "matter"}]])


def matters(doc: Doc) -> Iterator[Edit]:
    for span in matter_spans(doc):
        word = span[0]
        if is_verb(word) and not is_person(subject_of(word)):
            yield unmatter(doc[word.left_edge.i : word.i + 1])


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
