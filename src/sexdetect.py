import re


# ---------------------------------------------------------------------------
# Term lexicon. Each entry is (family, pattern, weight). A family is a word
# or phrase family; a sentence contributes the max weight among all of its
# patterns that match. Pattern weights scale roughly with how strongly a term
# signals sexual content.
# ---------------------------------------------------------------------------
SEXUAL_TERMS = [
    ("fuck", r"\bmother\s*fuck(?:er|ing)?\b", 2.0),
    ("fuck", r"\bfuck(?:ed|ing|er|s)?\b", 1.0),
    ("fuck", r"\bfuck(?:ed|ing)?\s+(?:her|him|me|us|them)\b", 1.8),
    ("finger", r"\bfinger(?:ed|ing)?\s+(?:her|him|me|us|them|my)\b", 2.0),
    ("cunt", r"\bcunts?\b", 3.0),
    ("pussy", r"\bpuss(?:y|ies)\b", 3.0),
    ("cock", r"\bcocks?\b", 2.0),
    ("dick", r"\bdicks?\b", 2.0),
    ("tits", r"\btits?\b", 2.0),
    ("breasts", r"\bbreasts?\b", 1.2),
    ("nipple", r"\bnipples?\b", 1.8),
    ("asshole", r"\b(?:ass|arse)holes?\b", 2.0),
    ("ass", r"\b(?:ass|arse)s?\b", 0.9),
    ("sex", r"\bsex\b", 1.0),
    ("sex", r"\bsex(?:ual|y|uality|es)\b", 1.2),
    ("sex toy", r"\bsex\s+toy(?:s)?\b", 2.5),
    ("intercourse", r"\bintercourse\b", 2.0),
    ("blowjob", r"\bblow\s?jobs?\b", 3.0),
    ("handjob", r"\bhand\s?jobs?\b", 3.0),
    ("rimjob", r"\brim\s?jobs?\b", 3.0),
    ("masturbat", r"\bmasturbat\w*", 3.0),
    ("cum", r"\bcum\w*", 3.0),
    ("ejaculat", r"\bejaculat\w*", 3.0),
    ("orgasm", r"\borgasm\w*", 2.2),
    ("penetrat", r"\bpenetrat\w*", 2.2),
    ("vagina", r"\bvagina\w*", 2.5),
    ("penis", r"\bpenis\w*", 2.5),
    ("clitoris", r"\bclitor\w*", 3.0),
    ("foreplay", r"\bforeplay\b", 1.8),
    ("erection", r"\berections?\b", 1.8),
    ("anal", r"\banal\b", 1.5),
    ("oral", r"\boral\s+sex\b", 2.5),
    ("erotic", r"\berotic\w*", 1.5),
    ("porn", r"\bporn\w*", 2.5),
    ("nude", r"\bnud(?:e|ity|es)\b", 0.5),
    ("naked", r"\bnaked\b", 0.5),
    ("lingerie", r"\blingerie\b", 0.5),
    ("prostitut", r"\bprostitut\w*", 1.5),
    ("whore", r"\bwhores?\b", 2.0),
    ("slut", r"\bsluts?\b", 1.5),
    ("rape", r"\brap(?:e|ing|ed|es)\b", 2.2),
    ("incest", r"\bincest\w*", 2.5),
    ("pedophile", r"\bped\w*phile\w*", 2.5),
    ("sodom", r"\bsodom\w*", 2.2),
    ("orgy", r"\borg(?:y|ies)\b", 2.0),
    ("fetish", r"\bfetish\w*", 1.5),
    ("fellatio", r"\bfellatio\b", 3.0),
    ("cunnilingus", r"\bcunnilingus\b", 3.0),
    ("dildo", r"\bdildo\w*", 3.0),
    ("vibrator", r"\bvibrators?\b", 2.5),
    ("bondage", r"\bbondage\b", 1.8),
    ("bdsm", r"\b(?:bdsm|s&m|sadomasochist\w*)\b", 2.0),
    ("swinger", r"\bswingers?\b", 1.5),
    ("concubine", r"\bconcubin\w*", 2.0),
    ("pimp", r"\bpimps?\b", 1.0),
    ("make love", r"\b(?:make|made|making|makes)\s+love\b", 1.8),
    ("virginity", r"\bvirginity\b", 1.0),
    ("seduct", r"\bseduct\w*", 1.2),
    ("stripper", r"\bstrippers?\b", 1.2),
    ("topless", r"\btopless\b", 1.0),
    ("strip club", r"\bstrip\s+(?:club|joint)s?\b", 1.5),
    ("pervert", r"\bpervert\w*|\bpervs?\b", 1.0),
    ("debauch", r"\bdebauch\w*", 1.2),
    ("libido", r"\blibido\b", 0.8),
    ("aphrodisiac", r"\baphrodisiac\w*", 0.8),
]

# Context patterns that reduce a matched family's contribution to a lower
# weight (e.g. "fuck" used purely as an interjection rather than sexually).
DOWNGRADES = [
    ("fuck", r"\b(?:what|who|why|where|how|when|which)\s+the\s+fuck\b", 0.15),
    ("fuck", r"\bthe\s+fuck(?:ing)?\b", 0.2),
    ("fuck", r"\bfuck\s+(?:you|yeah|no|yes|yep|nope)\b", 0.2),
    ("fuck", r"\bfucking\s+hell\b", 0.2),
    ("fuck", r"\bfucked\s+up\b", 0.2),
    ("fuck", r"\bfucking\s+(?:awesome|great|amazing|brilliant|beautiful|good|awful|worst|terrible)\b", 0.2),
    ("fuck", r"\b(?:this|that|my|your|his|her|our|their|the|a|an|some)\s+fucking\b", 0.2),
    ("fuck", r"\bholy\s+fuck(?:ing)?\b", 0.3),
    ("fuck", r"\b(?:goddamn|damn|aw|oh)\s+fuck(?:ing)?\b", 0.2),
]

# Context patterns that mark a matched family as innocent (contribution drops
# to zero, e.g. "pussy cat", donkey "ass", rooster "cock").
NULLIFIERS = [
    ("pussy", r"\bpussy\s+cat\b|\bpussies\b|\b(?:poor|dear|dear little)\s+pussy\b"),
    ("cock", r"\bcocks?\b(?=.*\bcrow(?:ed|ing|s)?\b)|\b(?:rooster|cockerel)s?\b"),
    ("dick", r"\bdicks?\s+(?:around|with)\b|\bclever\s+dick\b"),
    ("tits", r"\btit-?\s*for\s*-?tat\b|\btit-?tat-?toe\b|\btitmous\w*\b|\btitular\b"),
    ("ass", r"\blittle\s+(?:ass|arse)\b|\bdonkey\b"),
    ("sex", r"\bsame\s*[- ]?sex\b|\bsexism\b|\bsex(?:ual)?\s+(?:education|health|offender|offenders|discrimination|harassment|orientation|worker|workers)\b"),
    ("cum", r"\bcum(?:in|ulative|bers?)\b"),
]

_COMPILED_TERMS = [(f, re.compile(p, re.I), w) for f, p, w in SEXUAL_TERMS]
_COMPILED_DOWNGRADES = [(f, re.compile(p, re.I), w) for f, p, w in DOWNGRADES]
_COMPILED_NULLIFIERS = [(f, re.compile(p, re.I)) for f, p in NULLIFIERS]

_CAP = 0.99
_ABBREVIATIONS = r"(?:Mr|Mrs|Ms|Dr|St|Jr|Sr|vs|etc|e\.g|i\.e|Fig|Capt|Lt|Col|Gen|Prof|Rev)"
_DOT = "\ue000"


def split_sentences(text: str) -> list[str]:
    """Split `text` into sentences, stripping HTML tags and entities first."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[#a-zA-Z0-9]+;", " ", text)
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\b(\d+)\.(\d+)\b", rf"\1{_DOT}\2", text)
    text = re.sub(rf"(\b(?:{_ABBREVIATIONS}))\.", rf"\1{_DOT}", text)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.replace(_DOT, ".").strip() for s in sentences if s.strip()]


def sentence_probability(sentence: str) -> float:
    """Return the probability (0.0-1.0) that `sentence` contains sexual material."""
    weights = {}
    for family, pattern, weight in _COMPILED_TERMS:
        if pattern.search(sentence) and weight > weights.get(family, 0.0):
            weights[family] = weight
    for family, pattern, weight in _COMPILED_DOWNGRADES:
        if family in weights and pattern.search(sentence) and weight < weights[family]:
            weights[family] = weight
    for family, pattern in _COMPILED_NULLIFIERS:
        if family in weights and pattern.search(sentence):
            del weights[family]

    total = sum(weights.values())
    if total == 0:
        return 0.0
    return min(_CAP, 1.0 - (1.0 / (2.0 ** total)))


def sexual_probability(text: str, aggregate: str = "max") -> float:
    """Return the probability (0.0-1.0) that `text` contains sexual material.

    `text` is split into sentences and each is scored independently.
    `aggregate` controls how the per-sentence probabilities are combined:
      "max"  (default) - the most sexual sentence
      "mean"           - the average across sentences
    """
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    probs = [sentence_probability(s) for s in sentences]
    if aggregate == "mean":
        return sum(probs) / len(probs)
    return max(probs)