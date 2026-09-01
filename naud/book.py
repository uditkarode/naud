"""The words. Each table maps a phrase, written in base form, to what happens to it.
A word is said instead (verbs bend to fit, so `uses` and `used`), CUT drops it, LOOK only points
at it, and KEEP leaves it alone, so `real estate` survives the ban on `real`."""
from typing import Literal

from .edit import Kind

Entry = str | Literal[Kind.CUT, Kind.LOOK, Kind.KEEP]
Words = dict[str, Entry]

# How much is too much, from ASD-STE100 (Simplified Technical English), Issue 9.
WORDS: int = 20  # per sentence. Rule 5.1 says 20 for instructions, rule 6.3 says 25 for description.
SENTENCES: int = 6  # per paragraph, rule 6.6.


def gone(*phrases: str) -> Words:
    return {p: Kind.CUT for p in phrases}


def look(*phrases: str) -> Words:
    return {p: Kind.LOOK for p in phrases}


def keep(*phrases: str) -> Words:
    return {p: Kind.KEEP for p in phrases}


def opener(*phrases: str) -> Words:
    """`The point is that X`, `The point is, X`, `The point is: X` → `X`."""
    return {f"{p}{f}": Kind.CUT for p in phrases for f in (" that", ",", ":")}


# Whole phrases, taken as one. They are settled first, so no other rule can take a bite out of one.
IDIOMS: Words = {
    f"{asks} your word{rest}": "I want you to check"
    for asks in ("that need", "that needs", "this needs") for rest in ("", ", not mine")
}

# Emphasis. AI emphasises everything, so all of it goes. "very important" stays as the one way to mark weight.
EMPHASIS: Words = gone(
    "real", "genuine", "actual", "honest", "exact", "legit",
    "really", "truly", "literally", "absolutely", "incredibly", "deeply", "fundamentally",
    "genuinely", "honestly", "actually", "quietly", "crucially", "critically", "importantly",
    "notably", "remarkably", "profoundly", "utterly", "very", "extremely", "super", "highly",
    "massively", "hugely", "wildly", "insanely", "seriously", "definitely", "certainly",
    "clearly", "obviously", "essentially", "basically", "completely", "entirely", "totally",
) | {
    "the whole": "the", "the entire": "the", "be exactly": "be", "the exact same": "the same",
    **{f"not {adv}": "not quite" for adv in ("really", "completely", "entirely", "totally")},
    **{f"the right {n}": f"the {n}" for n in "way question answer tool time call move thing approach choice decision".split()},
    **{f"{adv} {w}": w for adv in ("exactly", "precisely") for w in "this that these those the what why how where when who which like as right because".split()},
} | keep(
    "real estate", "real time", "real-time", "real number", "real numbers", "in real life",
    "very important", "extremely important", "honest with",
)

# Throat-clearing. Says nothing, so nothing replaces it.
FILLER: Words = gone(
    "at the end of the day", "at its core", "when all is said and done",
    "it's worth noting that", "it is worth noting that", "it's worth noting", "it is worth noting",
    "worth noting that", "worth noting", "it's worth mentioning that", "it is worth mentioning that",
    "it's important to note that", "it is important to note that", "it's important to note", "it is important to note",
    "here's the thing", "here is the thing", "here's where it gets interesting", "here is where it gets interesting",
    "to be clear", "let me be clear", "make no mistake", "to be honest", "in all honesty", "to be fair",
    "let's break it down", "let's break this down", "it cannot be overstated",
    "great question", "good question", "excellent question", "hope this helps", "hope that helps",
    "needless to say", "it goes without saying that", "it goes without saying", "as you can see",
    "one important thing", "one thing to note", "one thing to watch for", "worth being clear",
    "one important thing to flag", "one important thing to mention", "one thing to flag", "one thing to mention",
    "bottom line", "in a nutshell", "long story short", "simply put", "put simply",
) | opener(
    "the point is", "the thing is", "the bottom line is", "the truth is", "the fact is",
    "the honest answer is", "the honest take is", "the honest version is", "the real fact is", "the short answer is",
    "the key thing is", "the important thing is", "the main thing is",
)

# Verbs borrowed from other trades that are also nouns, so only when used as verbs: "the surface" is safe.
VERBS: Words = {
    "leverage": "use", "harness": "use", "surface": "show", "underscore": "show", "dive into": "look at",
    "foster": "help", "assist": "help", "compound": "grow", "bump into": "run into", "endeavor": "try",
    "attempt": "try", "purchase": "buy", "flag": "mention", "exercise": "run", "contend for": "compete for",
    "eyeball": "check", "tear down": "clean up", "bake into": "build into", "close out": "finish",
    "cost you": "lose you", "cost nothing": "lose nothing", "buy you": "give you", "buy nothing": "gain nothing",
    **look("circle back", "double down", "lean into", "sit with", "reach for", "arrive at", "come back to", "unlock", "empower", "elevate"),
}

# Hard words with easy twins, and hype adjectives that say nothing.
LINKERS: dict[str, str] = {
    "however": "but", "therefore": "so", "thus": "so", "hence": "so", "consequently": "so",
    "additionally": "also", "furthermore": "also", "moreover": "also", "nevertheless": "still",
    "nonetheless": "still", "subsequently": "then",
}
PLAIN: Words = {
    "utilize": "use", "unpack": "explain", "delve into": "look at", "delve": "look", "navigate": "handle",
    "facilitate": "help", "shed light on": "explain", "double-click on": "look at", "commence": "start", "say the word": "tell me", "say the word on": "tell me about",
    "ascertain": "find out", "demonstrate": "show", "obtain": "get", "terminate": "end", "pressure-test": "test",
    "in order to": "to", "prior to": "before", "due to the fact that": "because", "in the event that": "if",
    "at this point in time": "now", "a number of": "some", "the majority of": "most",
    "in spite of the fact that": "although", "despite the fact that": "although", "for the purpose of": "to",
    "on a daily basis": "daily", "in close proximity to": "near", "approximately": "about",
    "sufficient": "enough", "numerous": "many", "additional": "more", "initial": "first", "optimal": "best",
    "individual": "person", "regarding": "about", "concerning": "about", "assistance": "help",
    "utilization": "use", "methodology": "method", "myriad": "many", "a plethora of": "many",
    "realm": "area", "paradigm shift": "big change", "throughline": "theme", "lessons learned": "lessons",
    "comprehensive": "full", "an identical": "the same", "identical to": "the same as",
    "be identical": "be the same", "be identical to": "be the same as", "currently": "now", "typically": "usually", "converge": "settle", "hazard": "risk", "predate": "come before",
    "churn": "change", "churn out": "produce", "churn through": "work through",
    "introduce": "add", "preserve": "keep", "supersede": "replace",
    "canonical": "standard", "trivial": "simple", "trivially": "easily", "caveat": "catch", "cadence": "pace",
    "empirically": "by testing", "in flight": "running", "in-flight": "running", "cheap": "quick", "expensive": "slow",
    "it changes the story": "it is a significant detail", "it dictates the session": "it is a significant detail",
    "what needs a glance from you": "what you need to check", "because it changes what I do next": "please let me know",
    **keep("customer churn", "churn rate"),
    **LINKERS,
    **{f"{k},": v for k, v in LINKERS.items()},
    **gone("load-bearing", "transformative", "game-changing", "groundbreaking", "cutting-edge", "robust", "seamless", "intricate", "holistic", "pivotal"),
}

# The half after `not:` that says nothing on its own, so `A rather than B` drops B instead of marking it.
EMPTY: frozenset[str] = frozenset({
    "guess", "assume", "the symptom", "a theoretical one", "a theoretical problem",
})

# What naud can see but not fix blindly. It points, you rewrite.
LOOK: Words = look(
    "worth", "physics", "the shape of", "shape of", "the engine", "hit hardest", "hits the hardest", "land hardest",
    "the tell", "this matters", "it matters", "that matters", "because it matters", "can't stop thinking about",
    "double-click", "lean in", "come along", "dispatches from", "field notes", "best operators", "top practitioners",
    "first wave", "the only thing that", "hold that thought", "stays yours", "stay yours", "mature", "leave you with",
    "in my chest", "where I landed", "seen this movie before", "been here before", "turns on", "useful thing",
    "the useful part", "want you to see", "hit a nerve", "struck a nerve", "stuck with me", "stayed with me",
    "struck a chord", "wreck", "shatter", "obliterate", "what got me", "the thing that got me", "doing the work",
    "heavy lifting", "most people", "a lot of folks", "nobody I know", "settled question", "rides along", "rides on",
    "pave the way", "landscape", "testament to", "when it comes to", "this is where", "reflecting a broader trend",
    "marking a significant shift", "right-size", "north star", "true north", "strategic imperative", "key takeaway",
    "key takeaways", "tapestry", "it changes the task", "which brings me back to",
    "brings me back to", "brings us back to", "in summary", "in conclusion", "to summarize", "to sum up",
    "what this means for you", "the practical read", "game-changer", "supercharge", "synergy", "not that",
    "mechanism", "yank",
)
