"""The parser, and what an edit is. Every part of naud uses both."""
from typing import NamedTuple

import spacy

nlp = spacy.load("en_core_web_sm")


class Edit(NamedTuple):
    """Say `text` in place of text[start:end]. text=None means naud only points at it."""

    start: int
    end: int
    text: str | None
    rule: str

    def shift(self, by):
        return self._replace(start=self.start + by, end=self.end + by)

    def yields_to(self, kept):
        """True when an edit kept earlier already covers this ground."""
        if kept.text is None:
            return False
        if self.text is None:
            return kept.start <= self.start and self.end <= kept.end
        return self.start < kept.end and kept.start < self.end
