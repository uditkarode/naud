from collections.abc import Callable

import pytest

ALL = [
    ("All 11 issues are fixed.", "The 11 issues are fixed."),
    ("The run's journal keeps all 53 finished finder results.", "The run's journal keeps the 53 finished finder results."),
    ("All 1490 frontend tests still pass.", "The 1490 frontend tests still pass."),
    ("All required checks passed and the PR shows as mergeable.", "The required checks passed and the PR shows as mergeable."),
    ("Lint and all tests passed.", "Lint and the tests passed."),
    ("I merged develop locally and resolved all the conflicts.", "I merged develop locally and resolved the conflicts."),
    ("All my changes are pushed.", "My changes are pushed."),
    ("All of them hold only staging data.", "They hold only staging data."),
    ("Tell me whether to fix all of them in one PR.", "Tell me whether to fix them in one PR."),
    ("All of this used one-time start options.", "This used one-time start options."),
    ("I have copied all of their changes into this checkout.", "I have copied their changes into this checkout."),
    ("I'll merge and release once they all pass.", "I'll merge and release once they pass."),
    ("I need them all to pass before I can merge.", "I need them to pass before I can merge."),
    ("The card, chips and dots all live in this panel.", "The card, chips and dots are in this panel."),
    ("The page, the product images and the 3D figure all load.", "The page, the product images and the 3D figure load."),
    ("I'm extracting them all, with keys.", "I'm extracting them, with keys."),
    ("SSH and Screen Sharing are all off.", "SSH and Screen Sharing are off."),
    ("The fixes are all still here.", "The fixes are still here."),
    ("It's all in the README.", "It's in the README."),
    # where `all` stands for the noun, counts times, or means less than all
    ("All are ready, with 0 restarts.", "All are ready, with 0 restarts."),
    ("Auth reviewer done: 3 findings, all 3 confirmed.", "Auth reviewer done: 3 findings, all 3 confirmed."),
    ("Group 05 is done, with all 15 fixed.", "Group 05 is done, with all 15 fixed."),
    ("There are 3, all on the main branch.", "There are 3, all on the main branch."),
    ("That's all for now.", "That's all for now."),
    ("That's all there is.", "That's all there is."),
    ("It passed all 3 times when I ran it locally.", "It passed all 3 times when I ran it locally."),
    ("Not all tests pass.", "Not all tests pass."),
    ("I didn't fix all the bugs.", "I didn't fix all the bugs."),
    ("So 200 photos don't all fight for the connection at once.", "So 200 photos don't all fight for the connection at once."),
    ("The GPU was busy almost all the time.", "The GPU was busy almost all the time."),
    ("In that run all frontend tests passed.", "In that run all frontend tests passed."),
    # where the tagger reads the verb after `all` as a noun
    ("Expiry, cleanup, and PR close or unlabel all work as before.", "Expiry, cleanup, and PR close or unlabel all work as before."),
    # a phrase with a meaning of its own, half of a word, or a quoted name
    ("It runs in the background all the time.", "It runs in the background all the time."),
    ("It went all the way through to the worker.", "It went all the way through to the worker."),
    ("The last four screenshots are all the same image.", "The last four screenshots are all the same image."),
    ("I waited all day.", "I waited all day."),
    ("All kinds of errors show up.", "All kinds of errors show up."),
    ("By all means, try it.", "By all means, try it."),
    ("It happened all of a sudden.", "It happened all of a sudden."),
    ("We use them all over the app.", "We use them all over the app."),
    ("Click select-all before the results load.", "Click select-all before the results load."),
    ('Customers receive the store\'s "all customers" broadcasts.', 'Customers receive the store\'s "all customers" broadcasts.'),
]
AT_ALL = [
    ("It fails with no scroll at all.", "It fails with no scroll."),
    ("The outer page area no longer scrolls at all, so the menu stays put.", "The outer page area no longer scrolls, so the menu stays put."),
    ("Previews cannot receive LINE messages at all.", "Previews cannot receive LINE messages."),
    ("I'm swapping the detail for when the toast shows at all.", "I'm swapping the detail for when the toast shows at all."),
    ("It fits the plan not at all.", "It fits the plan not at all."),
]
ALWAYS = [
    ("It always keeps at least 3 GB of cache.", "It keeps at least 3 GB of cache."),
    ("A LIFF ID always starts with the ID of the channel that owns it.", "A LIFF ID starts with the ID of the channel that owns it."),
    ("The default account still always replies.", "The default account still replies."),
    ("The child field is always required.", "The child field is required."),
    ("Always run the tests first.", "Run the tests first."),
    ("It doesn't always work.", "It doesn't always work."),
    ("The text check almost always passes.", "The text check almost always passes."),
    ("The shared calendar has always done this.", "The shared calendar has always done this."),
    ("As always, the tests pass.", "As always, the tests pass."),
    ("It shows the always-visible logout warning.", "It shows the always-visible logout warning."),
    ("No emphasised words like always/never.", "No emphasised words like always/never."),
]
NEVER = [
    ("The video code never ran.", "The video code did not run."),
    ("I never opened the old pages.", "I did not open the old pages."),
    ("Production never emails that domain.", "Production does not email that domain."),
    ("A migration that has run never runs again.", "A migration that has run does not run again."),
    ("The health check never passed.", "The health check did not pass."),
    ("The database never got throttled.", "The database did not get throttled."),
    ("Messages that customers type never reach the staff.", "Messages that customers type do not reach the staff."),
    ("The addresses point at it once and never change.", "The addresses point at it once and do not change."),
    ("Your own server is never touched.", "Your own server is not touched."),
    ("The build cache has never been pruned.", "The build cache has not been pruned."),
    ("The row can never be claimed again.", "The row cannot be claimed again."),
    ("You expect one scroll, but it never does.", "You expect one scroll, but it does not."),
    ("Never change anything on your own server.", "Do not change anything on your own server."),
    ("It caps the build cache by age and never by size.", "It caps the build cache by age and not by size."),
    ("The worst case is the current look, never a broken layout.", "The worst case is the current look, not a broken layout."),
    ("The rules only set the flag and never clear it.", "The rules only set the flag and never clear it."),
    ("The text check almost never passes.", "The text check almost never passes."),
    ("Never mind, it works.", "Never mind, it works."),
    ("Delete never-verified accounts after some days.", "Delete never-verified accounts after some days."),
]


@pytest.mark.parametrize(("text", "expected"), ALL + AT_ALL + ALWAYS + NEVER)
def test_absolutes(cleaned: Callable[[str], str], text: str, expected: str) -> None:
    assert cleaned(text) == expected
