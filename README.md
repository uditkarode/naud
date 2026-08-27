# naud

Takes the AI-speak out of English. spaCy parses each sentence, rules decide what goes, and a
word book says what to say instead.

```
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/naud diff draft.md      # or lint, or clean. Reads stdin when there is no file.
.venv/bin/pytest && .venv/bin/mypy naud tests
```

It cuts emphasis and filler, swaps jargon for plain words, and drops `A rather than B` and
`not X, but Y` contrasts. Em dashes, colons and semicolons that glue clauses become full stops.
Sentences over 20 words are split at a clause join, and paragraphs over 6 sentences are broken
up (limits from ASD-STE100 rules 5.1, 6.3, 6.6). What it can't fix blindly it points at.
Code fences and inline code are never touched.

```
naud/
  edit.py            what an edit is (CUT, SAY, STOP, LOOK, KEEP), and how a span becomes one
  book.py            the words: what goes, what is said instead, what is only looked at
  rules/             one module per family, one Rule(name, find) each, in order of who wins
    contrast.py      `not X but Y`, `A rather than B`, `No X. No Y. Just Z.`, `It's not X. It's Y.`
    words.py         the book's tables, `lives in`, a bare `This`
    joints.py        dashes, colons, semicolons between clauses
    length.py        sentences over the word limit, paragraphs over the sentence limit
    grammar.py       what the parse says, in words the rules can use
    match.py         spaCy Matcher plumbing
  markdown.py        where the prose is, and how to read a line of it as plain text
  mend.py            what the edits leave behind: spaces, marks, articles, capitals
  engine.py          text in, text out
  parse.py           the parser, loaded on first use
```

Add a phrase to a table in `book.py` to ban it. Add a finder to a rules module and a `Rule`
to `rules/__init__.py` to catch a shape. Add a case to `tests/` for it.
