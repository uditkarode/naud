"""Ways to turn a matched span into an edit."""
from itertools import takewhile

from lemminflect import getInflection

from .core import Edit

SUBJECT = {"nsubj", "nsubjpass", "csubj", "expl"}


def flag(span, rule):
    return Edit(span.start_char, span.end_char, None, rule)


def cut(span, rule):
    """Drop a span. Take with it what it leaves stranded: adverbs, *stars* or a hyphen on it, a dangling comma, an empty sentence."""
    doc, s, e = span.doc, span.start, span.end
    while s > 0 and doc[s - 1].dep_ == "advmod" and s <= doc[s - 1].head.i < e:
        s -= 1
    while s > 0 and e < len(doc) and doc[s - 1].text == "*" and doc[e].text == "*":
        s, e = s - 1, e + 1
    if e < len(doc) and doc[e].text == "-" and not doc[e - 1].whitespace_:
        e += 1
    if e < len(doc) - 1 and doc[e].text in (",", ":") and doc[s].text != ",":
        e += 1
    if s == span.sent.start and e == span.sent.end - 1 and doc[e].is_punct:
        e += 1
    last = doc[e - 1]
    keep_space = (s > 0 and doc[s - 1].is_alpha and not doc[s - 1].whitespace_) or (e < len(doc) and doc[e].is_punct)
    return Edit(doc[s].idx, last.idx + len(last) + (0 if keep_space else len(last.whitespace_)), "", rule)


def bend(word, like):
    """Inflect `word` the way `like` is inflected, keeping its case."""
    if like.lemma_ == word:
        return like.text
    if like.tag_[:2] in ("VB", "NN"):
        word = (getInflection(word, like.tag_) or [word])[0]
    return word[0].upper() + word[1:] if like.is_title else word


def swap(span, words, rule):
    """Say `words` in place of the span."""
    first, *rest = words.split()
    return Edit(span.start_char, span.end_char, " ".join([bend(first, span[0]), *rest]), rule)


def glue(span, text, rule):
    """Say `text` in place of a span and the space on both sides of it."""
    doc, last = span.doc, span[-1]
    start = doc[span.start - 1].idx + len(doc[span.start - 1]) if span.start else span.start_char
    return Edit(start, last.idx + len(last) + len(last.whitespace_), text, rule)


def reach(span):
    """Stretch a span over the phrase hanging off its end, as far as the parse allows."""
    doc = span.doc
    if span.end == len(doc):
        return span
    first = doc[span.end]
    fits = lambda t: t.left_edge.i >= span.start and t.dep_ != "ROOT" and not any(c.dep_ in SUBJECT for c in t.children)
    end = max((t.right_edge.i + 1 for t in takewhile(fits, (first, *first.ancestors))), default=span.end)
    while end > span.end and doc[end - 1].is_punct:
        end -= 1
    return doc[span.start : end]
