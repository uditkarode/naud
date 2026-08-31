# naud

Takes the AI-speak out of English. spaCy parses each sentence, rules decide what goes, and a
word book says what to say instead.

```
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/naud diff draft.md      # or lint, or clean. Reads stdin when there is no file.
.venv/bin/naud serve naud.sock    # clean Claude Code's replies as they show, see below
.venv/bin/pytest && .venv/bin/mypy naud tests
```

It cuts emphasis and filler, swaps jargon for plain words, turns `A rather than B` into
`A (not: B)`, and drops `not X, but Y` contrasts. Em dashes, colons and semicolons that glue clauses become full stops.
Sentences over 20 words are split at a clause join, and paragraphs over 6 sentences are broken
up (limits from ASD-STE100 rules 5.1, 6.3, 6.6). What it can't fix blindly it points at.
Code fences and inline code are never touched.

```
naud/
  edit.py            what an edit is (CUT, SAY, STOP, LOOK, KEEP), and how a span becomes one
  book.py            the words: what goes, what is said instead, what is only looked at
  rules/             one module per family, one Rule(name, find) each, in order of who wins
    contrast.py      `not X but Y`, `A rather than B`, `No X. No Y. Just Z.`, `It's not X. It's Y.`
    words.py         the book's tables, `lives in`, `sits at`, `worth knowing`, `bites`, a bare `This`
    joints.py        dashes, colons, semicolons between clauses
    length.py        sentences over the word limit, paragraphs over the sentence limit
    grammar.py       what the parse says, in words the rules can use
    match.py         spaCy Matcher plumbing
  markdown.py        where the prose is, and how to read a line of it as plain text
  mend.py            what the edits leave behind: spaces, marks, articles, capitals
  engine.py          text in, text out, and a Stream that cleans text as it arrives
  serve.py           the server behind Claude Code's MessageDisplay hook
  parse.py           the parser, loaded on first use
```

## Claude Code

Claude Code hands each batch of lines of a reply to its `MessageDisplay` hook before drawing it.
`naud serve` answers that hook at a unix socket with the model loaded once, and `socat` carries
each batch over. Add this to `~/.claude/settings.json`, with the path of your `naud`:

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command",
      "command": "setsid -f /path/to/naud serve \"$XDG_RUNTIME_DIR/naud.sock\" >/dev/null 2>&1"}]}],
    "MessageDisplay": [{"hooks": [{"type": "command",
      "command": "socat -t10 - \"UNIX-CONNECT:$XDG_RUNTIME_DIR/naud.sock\" 2>/dev/null || setsid -f /path/to/naud serve \"$XDG_RUNTIME_DIR/naud.sock\" >/dev/null 2>&1"}]}]
  }
}
```

The session start warms the server up, and a batch that finds it gone starts it again.
Only what is drawn changes. The transcript, and what the model reads back, stay as written.

Turn `verbose` off, in `/config` or as `"verbose": false`. Claude Code draws the hook's text only
while verbose is off, so with it on a reply shows cleaned as it streams and then reverts to what
the model wrote.

macOS has no `setsid` and no `$XDG_RUNTIME_DIR`, and `socat` comes from `brew install socat`. The
socket goes in `$TMPDIR` instead, and `nohup` in a subshell detaches the server:

```json
{
  "hooks": {
    "SessionStart": [{"hooks": [{"type": "command",
      "command": "(nohup /path/to/naud serve \"${TMPDIR:-/tmp}/naud.sock\" >/dev/null 2>&1 &)"}]}],
    "MessageDisplay": [{"hooks": [{"type": "command",
      "command": "socat -t10 - \"UNIX-CONNECT:${TMPDIR:-/tmp}/naud.sock\" 2>/dev/null || (nohup /path/to/naud serve \"${TMPDIR:-/tmp}/naud.sock\" >/dev/null 2>&1 &)"}]}]
  }
}
```

Add a phrase to a table in `book.py` to ban it. Add a finder to a rules module and a `Rule`
to `rules/__init__.py` to catch a shape. Add a case to `tests/` for it.
