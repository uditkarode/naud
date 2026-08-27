"""Where the prose is in a markdown file, and how to read a line of it as plain text."""
import re
from collections.abc import Iterator

FENCE = re.compile(r"^[ \t]*(```|~~~)(?!.*\1)", re.M)
INLINE = re.compile(r"(`[^`\n]*`)")
PREFIX = re.compile(r"[ \t]*(?:(?:[-*+]|\d+[.)]|#{1,6}|>)[ \t]+)*")
CURLY = str.maketrans("’“”", "'\"\"")


def blanked(m: re.Match[str]) -> str:
    """The same length, with nothing to parse."""
    return re.sub(r"\S", " ", m.group())


def lines(text: str, fenced: bool = False) -> Iterator[tuple[int, str]]:
    """(offset, line) for every line of prose: outside code fences, past any bullet or heading mark."""
    for m in re.finditer(r".+", text):
        if FENCE.match(m.group()):
            fenced = not fenced
        elif not fenced:
            prose = PREFIX.sub("", m.group(), count=1)
            if prose.strip():
                yield m.end() - len(prose), prose


def ends_fenced(text: str, fenced: bool = False) -> bool:
    """Whether the text ends inside a code fence, given whether it began in one."""
    return fenced != (len(FENCE.findall(text)) % 2 == 1)


def as_plain(line: str) -> str:
    """The line as the parser should see it, with inline code blanked and curly quotes straightened. Offsets stay the same."""
    return INLINE.sub(blanked, line).translate(CURLY)


def pieces(line: str) -> list[str]:
    """The line split into prose and inline code, code at the odd indexes."""
    return INLINE.split(line)
