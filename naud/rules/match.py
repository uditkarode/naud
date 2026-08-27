"""spaCy Matcher plumbing: phrases become token patterns, patterns become finders."""
from collections.abc import Callable, Iterator
from functools import cache
from typing import Any

from spacy.matcher import Matcher
from spacy.tokens import Doc, Span

from ..edit import Edit, Finder
from ..parse import model, parse

Pattern = list[dict[str, Any]]
Patterns = Callable[[], list[Pattern]]
Fix = Callable[[Span], Edit]


def pattern(phrase: str, pos: str | None = None) -> Pattern:
    """A phrase as a token pattern: the first word by lemma (`live in` finds `lives in`), the rest as written."""
    first, *rest = parse(phrase)
    head: dict[str, Any] = {"LEMMA": first.lemma_}
    if pos:
        head["POS"] = pos
    return [head, *({"LOWER": t.lower_} for t in rest)]


def spans(patterns: Patterns) -> Callable[[Doc], list[Span]]:
    """Every span the patterns match. The matcher is built on first use."""

    @cache
    def matcher() -> Matcher:
        built = Matcher(model().vocab)
        built.add("match", patterns())
        return built

    def find(doc: Doc) -> list[Span]:
        return [doc[start:end] for _, start, end in matcher()(doc)]

    return find


def matching(patterns: Patterns, fix: Fix) -> Finder:
    """A finder that hands every match of the patterns to `fix`."""
    find = spans(patterns)

    def rule(doc: Doc) -> Iterator[Edit]:
        return map(fix, find(doc))

    return rule
