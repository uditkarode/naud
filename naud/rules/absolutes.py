"""Rules about absolutes: `all` where the sentence already says it, `at all` after a `no`, `always`, and `never`
said as `not`."""
from collections.abc import Iterator

from spacy.tokens import Doc, Token

from ..edit import Edit, base, cut, replace, say
from .grammar import as_span, has_aux, is_subject, is_verb, negated, subject_of
from .words import quoted

HEDGES = frozenset({"not", "almost", "nearly", "virtually", "practically", "hardly", "roughly", "about", "around", "quite", "mostly"})
DETERMINERS = frozenset({"the", "these", "those", "this", "that", "my", "your", "its", "our", "their", "his", "her"})
POINTERS = frozenset({"this", "that", "these", "those", "which", "whom"})
NOMINATIVE = {"them": "they", "us": "we", "you": "you", "it": "it"}
NOUNS = frozenset({"NOUN", "PROPN"})
VERBAL = frozenset({"VERB", "AUX"})


def neighbours(word: Token) -> tuple[Token | None, Token | None]:
    doc = word.doc
    return (doc[word.i - 1] if word.i else None), (doc[word.i + 1] if word.i + 1 < len(doc) else None)


def bound(word: Token) -> bool:
    """Half of a hyphenated word (`always-visible`, `select-all`), one of a pair (`always/never`), or the start of
    a quoted name (`the "all customers" broadcast`)."""
    before, after = neighbours(word)
    hyphen = (before is not None and before.text == "-" and not before.whitespace_) or (
        after is not None and after.text == "-" and not word.whitespace_
    )
    slash = any(t is not None and t.text == "/" for t in (before, after))
    return hyphen or slash or (before is not None and before.is_quote and not before.whitespace_) or quoted(as_span(word))


def verb_of(word: Token) -> Token:
    """The verb of the clause the word is in."""
    while word.pos_ not in VERBAL and word.head.i != word.i:
        word = word.head
    return word


def hedged(word: Token) -> bool:
    """`not all`, `almost always` and `they don't all pass` mean less than all, so the word stays."""
    before, _ = neighbours(word)
    return (
        (before is not None and before.lower_ in HEDGES)
        or any(c.dep_ in ("neg", "advmod") for c in word.children)
        or negated(word.head)
        or negated(verb_of(word))
    )


# `All 11 issues are fixed` → `The 11 issues are fixed`, `resolved all the conflicts` → `resolved the conflicts`,
# `All of them pass` → `They pass`, `they all pass` → `they pass`, and `are all green` → `are green`.
# Where `all` stands for the noun (`All are ready`, `all 3 confirmed`) the sentence needs it, so it stays.
def unall(word: Token) -> Edit | None:
    doc = word.doc
    before, after = neighbours(word)
    if after is None:
        return None
    if after.lower_ in DETERMINERS and after.dep_ in ("det", "poss"):
        return cut(as_span(word))
    if after.lower_ == "of":
        return all_of(word)
    if floats(word, before, after):
        return cut(as_span(word))
    if opens_phrase(before) and word.dep_ in COUNTING and names(counted(word), word) and after.lower_ != "such":
        return say(as_span(word), "the")
    if before is not None and before.lemma_ == "be" and predicate(after) and not points(doc, before):
        return cut(as_span(word))
    return None


def all_of(word: Token) -> Edit | None:
    """`all of them` is said `they` where it is the subject, `all of this` and `all of its changes` lose `all of`."""
    doc = word.doc
    if word.i + 2 >= len(doc):
        return None
    what = doc[word.i + 2]
    if what.lower_ in NOMINATIVE:
        return say(doc[word.i : what.i + 1], NOMINATIVE[what.lower_] if is_subject(word) else what.lower_)
    if what.lower_ in POINTERS or what.pos_ == "PROPN" or (what.dep_ in ("det", "poss") and what.lower_ not in ("a", "an")):
        return cut(doc[word.i : word.i + 2])
    return None


FLOAT_NEXT = frozenset({"VERB", "AUX", "NOUN", "ADV", "PART"})


def floats(word: Token, before: Token | None, after: Token) -> bool:
    """`all` after the noun it counts, as in `they all pass`, `the card, chips and dots all live here` and `I need
    them all to pass`, or after an object that ends the clause, as in `I fixed it all`. The tagger can read the
    verb after `all` as a noun (`the 3D figure all load`), so a noun there counts as the verb. A noun that ends a
    phrase opening the sentence is not counted, as in `In that run all tests passed` and `Today all tests pass`."""
    if before is None or before.pos_ not in NOUNS | {"PRON"} or before.dep_ in ("poss", "npadvmod"):
        return False
    if after.is_punct:
        return before.lower_ in NOMINATIVE and before.dep_ == "dobj"
    first = word.doc[word.sent.start]
    opening = first.pos_ == "ADP" and any(t.i == before.i for t in first.subtree)
    return after.pos_ in FLOAT_NEXT and not opening


def opens_phrase(before: Token | None) -> bool:
    """No word in front of `all` that it could count, so it opens a noun phrase. After a noun, `all` floats, and the
    tagger can call the verb after it a noun, as in `the 3D figure all load`."""
    return before is None or before.pos_ not in NOUNS | {"PRON", "NUM"}


COUNTING = frozenset({"det", "predet", "advmod", "quantmod"})


def counted(word: Token) -> Token:
    """The noun `all` counts. The parser can hang `all` on a number or a compound before it, as in `all 1490
    frontend tests`."""
    noun = word.head
    while noun.dep_ in ("nummod", "compound", "amod") and noun.head.i > noun.i:
        noun = noun.head
    return noun


def names(noun: Token, word: Token) -> bool:
    """A plural noun after `all` with no other determiner of its own, as in `all 7 tests`. A singular one is left
    alone, since the tagger reads the verb in `the build all work` as one, and so is a count of times, as in
    `passed all 3 times`."""
    return (
        noun.i > word.i
        and noun.tag_ in ("NNS", "NNPS")
        and noun.dep_ != "npadvmod"
        and not any(c.dep_ in ("det", "poss") and c.i != word.i for c in noun.children)
    )


PREDICATE_STOPS = frozenset({"there", "that", "but", "over", "along", "right", "too"})


def predicate(after: Token) -> bool:
    """What follows `is all`: an adjective, a place or a participle, as in `are all green`, `is all in the README`
    and `were all accepted`. `all over`, `all right` and `all but` mean something else."""
    return (after.pos_ in ("ADJ", "ADP", "ADV") or after.tag_ == "VBN") and after.lower_ not in PREDICATE_STOPS


def points(doc: Doc, be: Token) -> bool:
    """`That's all for now`: after a pointer word, `all` is what the sentence says."""
    return be.i > 0 and doc[be.i - 1].lower_ in POINTERS | {"what"}


def alls(doc: Doc) -> Iterator[Edit]:
    for word in doc:
        if word.lower_ == "all" and not bound(word) and not hedged(word):
            edit = unall(word)
            if edit is not None:
                yield edit


# `It fails with no scroll at all` → `It fails with no scroll`. Without a `no` before it in its clause, `at all`
# carries the sentence, as in `if it runs at all`, so it stays.
NEGATIVES = frozenset({"no", "not", "n't", "never", "nothing", "none", "nobody", "without", "neither", "nor"})


def at_all(doc: Doc) -> Iterator[Edit]:
    for word in doc[1:]:
        at = doc[word.i - 1]
        if word.lower_ != "all" or at.lower_ != "at" or (at.i and doc[at.i - 1].lower_ == "not"):
            continue
        if any(t.lower_ in NEGATIVES and t.i < at.i for t in verb_of(at).subtree):
            yield cut(doc[at.i : word.i + 1])


# `It always keeps 3 GB` → `It keeps 3 GB`. `has always done this` says since when, so it stays.
def perfect(verb: Token) -> bool:
    return any(c.dep_ == "aux" and c.lemma_ == "have" for c in verb.children)


def always(doc: Doc) -> Iterator[Edit]:
    for word in doc:
        if word.lower_ == "always" and word.head.i != word.i and not bound(word) and not hedged(word) and not perfect(word.head):
            yield cut(as_span(word))


# `The video code never ran` → `The video code did not run`, `is never touched` → `is not touched`, `can never` →
# `cannot`, `Never change it` → `Do not change it`, and `by age and never by size` → `by age and not by size`.
DO = {"VBZ": "does", "VBP": "do", "VBD": "did"}


def tense(verb: Token) -> str | None:
    """The tense of a verb that needs a `do` to be said with `not`. The tagger reads a past verb with no helper
    as a participle (`the check never passed`), a present one as a bare verb (`messages never reach`), and a verb
    as a plural noun (`production never emails`). A verb joined by `and` takes the tense of the one before it.
    `set` and `put` read the same in the past and the present, so their tense is not known."""
    if verb.tag_ == "VBD" and verb.lower_ == verb.lemma_:
        return None
    if verb.tag_ in DO:
        return verb.tag_
    if verb.tag_ == "VB" and not has_aux(verb) and subject_of(verb) is not None:
        return "VBP"
    if verb.tag_ == "VBN" and not has_aux(verb) and subject_of(verb) is not None:
        return "VBD"
    if verb.tag_ == "NNS" and is_verb(verb):
        return "VBZ"
    if verb.tag_ == "VB" and verb.dep_ == "conj":
        return tense(verb.head)
    return None


def ends(word: Token) -> bool:
    """The word ends its clause, as in `it never does.`"""
    return word.i + 1 == len(word.doc) or word.doc[word.i + 1].is_punct


def unnever(word: Token) -> Edit | None:
    doc = word.doc
    before, after = neighbours(word)
    if after is None or (before is not None and before.lower_ in HEDGES):
        return None
    if before is not None and (before.tag_ == "MD" or before.dep_ in ("aux", "auxpass") or before.lemma_ == "be"):
        return say(doc[before.i : word.i + 1], "cannot") if before.lower_ == "can" else replace(as_span(word), "not")
    opens = word.i == word.sent.start
    if opens and after.tag_ == "VB" and subject_of(after) is None:
        return replace(as_span(word), "Do not" if word.is_title else "do not")
    if not opens and (form := tense(after)) is not None:
        if after.lemma_ == "be" or (after.lemma_ in ("have", "do") and (after.dep_ in ("aux", "auxpass") or ends(after))):
            return replace(doc[word.i : after.i + 1], f"{after.text} not")
        return replace(doc[word.i : after.i + 1], f"{DO[form]} not {base(after)}")
    if after.pos_ in ("ADP", "DET") and word.head.pos_ not in VERBAL:
        return replace(as_span(word), "not")
    return None


def never(doc: Doc) -> Iterator[Edit]:
    for word in doc:
        if word.lower_ == "never" and not bound(word):
            edit = unnever(word)
            if edit is not None:
                yield edit
