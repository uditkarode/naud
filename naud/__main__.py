"""naud lint  [FILE]    what it would change, and where
naud clean [FILE]    the cleaned text
naud diff  [FILE]    before and after
naud serve SOCKET    answer Claude Code's MessageDisplay hook at SOCKET, so replies show cleaned
Reads stdin when there is no FILE."""
import difflib
import sys

from . import Kind, clean, lint, serve


def main() -> None:
    mode, *path = sys.argv[1:] or ["lint"]
    if mode == "serve":
        serve.main(path[0])
        return
    text = open(path[0]).read() if path else sys.stdin.read()
    if mode == "clean":
        print(clean(text), end="")
    elif mode == "diff":
        print("\n".join(difflib.unified_diff(text.splitlines(), clean(text).splitlines(), "before", "after", lineterm="", n=0)))
    else:
        for e in lint(text):
            print(f"{e.start:>7}  {e.rule:<9} {text[e.start:e.end]!r}", "(look at this)" if e.kind is Kind.LOOK else f"→ {e.text!r}")


if __name__ == "__main__":
    main()
