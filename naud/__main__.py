"""naud lint  [FILE]   what it would change, and where
naud clean [FILE]   the cleaned text
naud diff  [FILE]   before and after
Reads stdin when there is no FILE."""
import difflib
import sys

from . import clean, lint


def main() -> None:
    mode, *path = sys.argv[1:] or ["lint"]
    text = open(path[0]).read() if path else sys.stdin.read()
    if mode == "clean":
        print(clean(text), end="")
    elif mode == "diff":
        print("\n".join(difflib.unified_diff(text.splitlines(), clean(text).splitlines(), "before", "after", lineterm="", n=0)))
    else:
        for e in lint(text):
            print(f"{e.start:>7}  {e.rule:<9} {text[e.start:e.end]!r}", f"→ {e.text!r}" if e.text is not None else "(look at this)")


if __name__ == "__main__":
    main()
