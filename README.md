# naud

Takes the AI-speak out of English. spaCy parses each sentence, a handful of rules
(`naud/rules.py`) decide what goes, and a word book (`naud/book.py`) says what to say instead.

    python -m venv .venv && .venv/bin/pip install -e .
    .venv/bin/naud diff draft.md      # or: lint, clean. stdin when there is no file.

What it does: cuts emphasis and filler, swaps jargon for plain words, drops "A rather than B"
and "not X, but Y" contrasts, turns em dashes, colons and semicolons that glue clauses into
full stops, splits sentences over 20 words at a clause join, and breaks paragraphs over 6
sentences (limits from ASD-STE100 rules 5.1, 6.3, 6.6). What it can't fix blindly it points at.

Add a phrase to a table in `book.py` to ban it. Add a function to `RULES` to catch a shape.
Code fences and inline code are never touched.
