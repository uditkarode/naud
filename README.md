# naud

Takes the AI-speak out of English.

It cuts emphasis and filler, swaps jargon for plain words, turns `A rather than B` into
`A (not: B)`, and drops `not X, but Y` contrasts. Em dashes, colons and semicolons that glue
clauses become full stops. Long sentences are split, and long paragraphs are broken up. What it
can't fix blindly it points at. Code fences and inline code are never touched.

## Install

```
pip install git+https://github.com/uditkarode/naud
```

## Use

```
naud lint  draft.md    what it would change, and where
naud clean draft.md    the cleaned text
naud diff  draft.md    before and after
```

Each reads stdin when there is no file.

## Claude Code

`naud serve` cleans Claude Code's replies as they are drawn. The transcript, and what the model
reads back, stay as written.

Add this to `~/.claude/settings.json`, with the path of your `naud`. On Linux:

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

On macOS, with `socat` from `brew install socat`:

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

Turn `verbose` off, in `/config` or as `"verbose": false`. With it on, a reply shows cleaned as it
streams and then reverts to what the model wrote.
