"""The parser. Loaded once, the first time it is needed."""
from functools import cache

import spacy
from spacy.language import Language
from spacy.tokens import Doc


@cache
def model() -> Language:
    return spacy.load("en_core_web_sm")


def parse(text: str) -> Doc:
    return model()(text)
