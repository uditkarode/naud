from collections.abc import Callable

import pytest

from naud import lint

EMPHASIS = [
    ("Honestly, the real problem is the actual parser.", "The problem is the parser."),
    ("That is genuinely the whole point.", "That is the point."),
    ("This is exactly what we need.", "This is what we need."),
    ("The right way to do this is simple.", "The way to do this is simple."),
    ("So you got lucky, but not really lucky.", "So you got lucky, but not quite lucky."),
    ("Real estate is very important.", "Real estate is very important."),
    ("Per-output delay forces exactly this shape.", "Per-output delay forces this shape."),
    ("Your diagnosis was exactly right.", "Your diagnosis was right."),
    ("I checked exactly one file.", "I checked exactly one file."),
    ("It is completely buried, but not entirely.", "It is buried, but not quite."),
]
FILLER = [
    ("It's worth noting that the model works.", "The model works."),
    ("The honest answer is that it works.", "It works."),
    ("Great question! The point is that it works.", "It works."),
]
JARGON = [
    ("It leverages a robust model.", "It uses a model."),
    ("However, the whole approach compounds over time.", "But the approach grows over time."),
    ("Please utilize the tool in order to obtain the result prior to the meeting.", "Please use the tool to get the result before the meeting."),
    ("## Leverage the API", "## Use the API"),
    ("Reconcile compares the string against itself and doesn't churn.", "Reconcile compares the string against itself and doesn't change."),
    ("Less code churn means fewer bugs.", "Less code change means fewer bugs."),
    ("Customer churn is high.", "Customer churn is high."),
    ("It churns out code.", "It produces code."),
    ("The C trees are identical to what you have.", "The C trees are the same as what you have."),
    ("The trees are identical.", "The trees are the same."),
    ("It makes an identical copy.", "It makes the same copy."),
    ("Two identical copies.", "Two identical copies."),
    ("Output is byte-identical to before.", "Output is byte-identical to before."),
    ("BT currently plays late, as LDAC typically does.", "BT now plays late, as LDAC usually does."),
    ("The rate adjustment needs to converge.", "The rate adjustment needs to settle."),
    ("It predates the speaker.", "It comes before the speaker."),
    ("Just say the word and I'll do it.", "Just tell me and I'll do it."),
    ("Say the word on the timeout and I'll fix it.", "Tell me about the timeout and I'll fix it."),
]
LIVES = [
    ("The risk lives in the gap between them.", "The risk is in the gap between them."),
    ("My parents live in Tokyo.", "My parents live in Tokyo."),
    ("They live here.", "They live here."),
    ("BT sits at 0ms.", "BT is at 0ms."),
    ("Your 56 sits between 38 and 65.", "Your 56 is between 38 and 65."),
    ("The value has sat at zero.", "The value has been at zero."),
    ("Sit here.", "Sit here."),
]
WORTH = [
    ("Worth knowing: this deploy runs migration 17.", "This deploy runs migration 17."),
    ("Also worth knowing: the seeded account is gone.", "The seeded account is gone."),
    ("Worth saying plainly: this is cleanup.", "This is cleanup."),
    ("Two things worth knowing: your local Node is 26.", "Two things. Your local Node is 26."),
    ("One thing worth your call: the command line is stored.", "One thing: the command line is stored."),
    ("One deviation from prod worth flagging: prod had extensions.", "One deviation from prod: prod had extensions."),
    ("Both are worth fixing.", "Both need fixing."),
    ("It is genuinely worth fixing.", "It needs fixing."),
    ("You're right that it's worth fixing properly.", "You're right that it needs fixing properly."),
    ("The third has 6 cheap unit tests worth keeping.", "The third has 6 quick unit tests to keep."),
    ("The one thing worth keeping from it: the template.", "The one thing to keep from it: the template."),
    ("The template is worth keeping.", "The template needs keeping."),
    ("Worth fixing in OC Lab.", "Needs fixing in OC Lab."),
    ("Kept for rollback; worth deleting once the new one lands.", "Kept for rollback; needs deleting once the new one lands."),
    ("It is not worth doing.", "It is not worth doing."),
    ("It occupies a disk's worth of space.", "It occupies a disk's worth of space."),
]
BITE = [
    ("The 10-min cap will bite again on any slow install.", "The 10-min cap will cause a problem again on any slow install."),
    ("Let me verify the one thing that actually bites.", "Let me verify the one thing that causes a problem."),
    ("One thing that will keep biting: the lockfile.", "One thing that will keep causing a problem: the lockfile."),
    ("Only bites a recovered process.", "Only bites a recovered process."),
]
PLAINER = [
    ("Two things I want to flag.", "Two things I want to mention."),
    ("The PR itself exercises the new routing.", "The PR itself runs the new routing."),
    ("All five commands contend for the same data disk.", "All five commands compete for the same data disk."),
    ("The guest agent is baked into the image.", "The guest agent is built into the image."),
    ("Swarm services torn down, the volume removed.", "Swarm services cleaned up, the volume removed."),
    ("Raising it to 10s costs nothing.", "Raising it to 10s loses nothing."),
    ("Adding a logger would introduce a new pattern.", "Adding a logger would add a new pattern."),
    ("Caddy isn't preserving the header.", "Caddy isn't keeping the header."),
    ("This supersedes the earlier behavior.", "This replaces the earlier behavior."),
    ("Verifying the kernel-level cause empirically.", "Verifying the kernel-level cause by testing."),
    ("Trivial to narrow to that.", "Simple to narrow to that."),
    ("Both fixes are in flight now.", "Both fixes are running now."),
    ("Start it if you want to eyeball the behavior.", "Start it if you want to check the behavior."),
    ("Let me close out the remaining work.", "Let me finish the remaining work."),
    ("That closes out the migration.", "That finishes the migration."),
    ("Close out of the app and reopen it.", "Close out of the app and reopen it."),
    ("Canonical build scripts exist.", "Standard build scripts exist."),
    ("Nightly is just the refresh cadence.", "Nightly is just the refresh pace."),
]
HYPE = [
    ("One important thing to flag.", ""),
    ("The legit thing is that the cause is in the stack.", "The thing is that the cause is in the stack."),
    ("It isn't small, it changes the story.", "It isn't small, it is a significant detail."),
    ("This needs your opinion, because it dictates the session.", "This needs your opinion, because it is a significant detail."),
    ("What needs a glance from you is the plan.", "What you need to check is the plan."),
    ("Two things that need your word, not mine.", "Two things I want you to check."),
    ("One thing that needs your word, not mine:", "One thing I want you to check:"),
    ("Two things that need your word:", "Two things I want you to check:"),
    ("This needs your word, not mine.", "I want you to check."),
]
STRANDED = [
    ("the **real** problem", "the problem"),
    ("There are two genuinely-different routes.", "There are two different routes."),
    ("Playing straight at the TV is a perfectly real path.", "Playing straight at the TV is a path."),
]


@pytest.mark.parametrize(("text", "expected"), EMPHASIS + FILLER + JARGON + LIVES + WORTH + BITE + PLAINER + HYPE + STRANDED)
def test_words(cleaned: Callable[[str], str], text: str, expected: str) -> None:
    assert cleaned(text) == expected


@pytest.mark.parametrize(("text", "rule"), [
    ("The data is real.", "emphasis"),
    ('The word "real" is banned.', "emphasis"),
    ("Which brings me back to the parser.", "look"),
    ("CI was still running, worth a glance before you trust the deploy.", "worth"),
    ("The stated mechanism is wrong.", "look"),
    ("This means the parser is slow.", "vague"),
])
def test_only_pointed_at(cleaned: Callable[[str], str], looks: Callable[[str], set[str]], text: str, rule: str) -> None:
    assert cleaned(text) == text
    assert rule in looks(text)


def test_half_a_hyphenated_word_is_kept() -> None:
    assert lint("It is near-identical.") == []


def test_a_bare_this_is_vague_but_a_determiner_is_not(looks: Callable[[str], set[str]]) -> None:
    assert "vague" in looks("This is where it gets interesting.")
    assert "vague" not in looks("That bug is old.")
