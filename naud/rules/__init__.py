"""The rules, in order. Where two edits overlap, the earlier rule wins."""
from dataclasses import dataclass

from .. import book
from ..edit import Finder
from . import contrast, joints, length, words


@dataclass(frozen=True)
class Rule:
    name: str
    find: Finder


RULES: list[Rule] = [
    Rule("cleft", contrast.cleft),
    Rule("tail", contrast.tail),
    Rule("staccato", contrast.staccato),
    Rule("not-but", contrast.not_but),
    Rule("not-that", contrast.not_that),
    Rule("filler", words.table(book.FILLER)),
    Rule("emphasis", words.table(book.EMPHASIS)),
    Rule("jargon", words.table(book.VERBS, pos="VERB")),
    Rule("plain", words.table(book.PLAIN)),
    Rule("lives", words.lives),
    Rule("look", words.table(book.LOOK)),
    Rule("vague", words.vague),
    Rule("dash", joints.dashes),
    Rule("colon", joints.colons),
    Rule("split", length.split),
    Rule("long", length.long),
    Rule("paragraph", length.paragraphs),
]
