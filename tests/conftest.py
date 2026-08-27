from collections.abc import Callable

import pytest

from naud import Kind, clean, lint


@pytest.fixture
def looks() -> Callable[[str], set[str]]:
    """The rules that only pointed at something in the text."""
    return lambda text: {e.rule for e in lint(text) if e.kind is Kind.LOOK}


@pytest.fixture
def cleaned() -> Callable[[str], str]:
    return clean
