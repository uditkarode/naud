from collections.abc import Callable

import pytest

DASHES = [
    ("Found it — the Bash tool runs zsh.", "Found it. The Bash tool runs zsh."),
    ("Good — that settles it.", "Good. That settles it."),
    ("The kernel side works fine — what's missing is userspace.", "The kernel side works fine. What's missing is userspace."),
    ("**1.52.3** — and it's also the newest.", "**1.52.3**. And it's also the newest."),
    ("We — the team — shipped it.", "We, the team, shipped it."),
    ("But before you do — this is a decision.", "But before you do, this is a decision."),
    ("It vendors libuv 1.52.1 — identical to what you have.", "It vendors libuv 1.52.1, identical to what you have."),
    ("Set it up — including a toggle if you want both.", "Set it up, including a toggle if you want both."),
    ("Between 2019–2021 it grew.", "Between 2019–2021 it grew."),
]
COLONS = [
    ("Two things to fix: the script reported garbage as fact.", "Two things to fix. The script reported garbage as fact."),
    ("The difference: the BT leg is now attached.", "The difference: the BT leg is now attached."),
    ("The parser reads the text; the rules run after that.", "The parser reads the text. The rules run after that."),
    ("Turn it on; turn it off.", "Turn it on. Turn it off."),
]


@pytest.mark.parametrize(("text", "expected"), DASHES + COLONS)
def test_joints(cleaned: Callable[[str], str], text: str, expected: str) -> None:
    assert cleaned(text) == expected
