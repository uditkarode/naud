# naud

## What this is

naud takes the AI-speak out of English. It reads prose, decides which words and shapes are
padding, and rewrites them into plain speech. It runs over a file or over stdin, and it runs as a
long-lived server that cleans Claude Code's replies as they are drawn on screen.

It is not a spell checker and not a style linter that scores you. It edits.

## What it is for

Models write in a recognisable way. They emphasise everything, open with throat-clearing, reach
for a hard word when an easy one exists, and say what a thing is not before saying what it is.
Prose full of that is slower to read and says less than it looks like it says. naud removes the
habit from the text without the writer having to notice each instance.

Two ways it gets used:

* Over text you own, as a pass on a draft, a README, a commit message, or docs.
* Over a live Claude Code session, where it rewrites each reply as it streams. Only what is drawn
  changes. The transcript, and what the model reads back on the next turn, stay as written, so
  cleaning never alters the conversation itself.

## How it thinks about the job

Every rule proposes edits over a parsed sentence, and the engine picks which ones survive. The
parse is what makes this more than find-and-replace. A rule can ask whether a word is a verb here,
whether a clause has its own subject, whether a phrase hangs off the one before it. That is how
`the surface` survives a ban on `surface` the verb, and how a dash between two standing clauses
becomes a full stop while a dash inside a parenthetical becomes a comma.

An edit is one of a small set of kinds. Some cut a span, some say it another way, some end a
sentence there, and one only points. That last kind is the important one. When naud can see a
problem but cannot fix it without guessing what the writer meant, it refuses to guess and marks
the place instead. A rewrite that changes meaning is worse than no rewrite, so anything ambiguous
becomes something the writer is shown and left to rewrite.

Rules are ordered, and the earlier rule wins where two edits cover the same ground. Ordering
settles every conflict, so where a new rule goes in the list is a decision to think about.

## What it promises

* Code is never touched. Fenced blocks and inline spans pass through untouched, and the parser is
  fed a version with code blanked out so it cannot mistake code for prose.
* Markdown structure survives. Bullet marks, headings, and quote marks are stepped over, and a
  paragraph split in two keeps the indent of the bullet it belongs to.
* It works on one line of prose at a time. Rules cannot see across lines, which keeps offsets
  simple and streaming possible, and means anything needing whole-document context is out of
  scope by construction.
* Text arriving in pieces is handled. The streaming path remembers whether it is inside a code
  fence between batches, and the server puts a message's batches back in order when they arrive
  out of order.
* A replacement is bent to fit where it lands, so a swap keeps the tense, number, and capital of
  the word it replaced, and the articles and spacing left behind are mended afterwards.

## Where the rules come from

Two sources, and they answer different questions.

The limits on length come from ASD-STE100, Simplified Technical English, the aerospace writing
standard. It is the reason there is a word cap on sentences and a sentence cap on paragraphs, and
the reason those numbers are what they are.

The word lists come from reading AI replies and writing down what kept appearing. They record
habits seen in model output. They are not a general English style guide, so a phrase belongs in
them when a model overuses it, and not when someone dislikes it. Each list has a stance behind it.
Emphasis words go because a model emphasises everything, filler goes because it says nothing, hard
words are swapped for easy twins, and phrases that only a human can rewrite are pointed at.

Entries carry exceptions with them. A ban on a word has to survive the places where the word is
correct, which is why the lists also hold things to leave alone.

## Conventions

Docstrings and comments are written in the plain English the tool enforces. Short, concrete, about
what the code does and why, never about what it used to do or what path was not taken. If a
comment would read as AI-speak, it is wrong for this codebase.

Tests are tables of before-and-after pairs taken from sentences models wrote. A new rule, a new
word, or a new exception comes with the sentence that motivated it, including the near-miss
sentence that must stay untouched. The near-miss is the point. Most of the difficulty here is not
catching the bad case, it is leaving the good one alone.

The code is fully typed and checked strictly. Keep it that way.
