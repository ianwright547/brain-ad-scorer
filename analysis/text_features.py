"""Deterministic text analysis for ad copy.

Everything in this module is computed locally — no API calls, no ML.
These metrics act as a free "pre-flight check" that runs before spending
money on an LLM evaluation, and they're displayed alongside the expert
scores so the two can be compared.
"""

import re
from collections import Counter

# Lexicons are intentionally small and curated by hand. A word earns its
# place here because direct-response copywriting treats it as a known
# trigger, not because it appeared in some scraped frequency list.

POWER_WORDS = {
    "free", "proven", "guaranteed", "instantly", "secret", "exclusive",
    "unlock", "discover", "transform", "results", "save", "boost",
    "effortless", "breakthrough", "premium", "elite", "insider",
}

URGENCY_WORDS = {
    "now", "today", "tonight", "hurry", "deadline", "expires", "closing",
    "limited", "last", "final", "ends", "only", "before", "spots", "left",
}

RISK_REVERSAL_PHRASES = [
    "money back", "money-back", "refund", "guarantee", "guaranteed",
    "no risk", "risk-free", "risk free", "free trial", "cancel anytime",
    "no obligation", "no questions asked", "pay nothing",
]

CTA_VERBS = {
    "buy", "shop", "order", "get", "grab", "claim", "book", "schedule",
    "call", "text", "click", "tap", "sign", "join", "start", "try",
    "download", "register", "subscribe", "apply", "visit", "dm", "comment",
}

# Specificity signals: concrete numbers beat vague claims. Each pattern
# catches a different way copy gets concrete.
RE_MONEY = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?[km]?", re.IGNORECASE)
RE_PERCENT = re.compile(r"\d+(?:\.\d+)?\s?%")
RE_TIMEFRAME = re.compile(
    r"\b\d+\s?(?:minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
RE_NUMBER = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")

RE_SENTENCE_SPLIT = re.compile(r"[.!?]+(?:\s|$)")
RE_WORD = re.compile(r"[a-zA-Z']+")

VOWELS = set("aeiouy")


def count_syllables(word):
    """Estimate syllables by counting vowel groups.

    The heuristic: each contiguous run of vowels is one syllable, a
    trailing silent 'e' doesn't count ("make" is 1, not 2), and every
    word has at least one. This is the standard approximation used when
    a pronunciation dictionary isn't available — accurate within ~1
    syllable for the vast majority of English words.
    """
    word = word.lower().strip("'")
    if not word:
        return 0

    groups = 0
    prev_was_vowel = False
    for ch in word:
        is_vowel = ch in VOWELS
        if is_vowel and not prev_was_vowel:
            groups += 1
        prev_was_vowel = is_vowel

    if word.endswith("e") and not word.endswith(("le", "ee")) and groups > 1:
        groups -= 1

    return max(groups, 1)


def split_sentences(text):
    parts = RE_SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


def flesch_scores(words, sentences):
    """Flesch Reading Ease and Flesch-Kincaid Grade Level.

    Both formulas combine the same two ratios — words per sentence and
    syllables per word — with different published coefficients. Ad copy
    should land around 70+ ease / grade 6 or below: people skim feeds,
    they don't study them.
    """
    if not words or not sentences:
        return None, None

    total_syllables = sum(count_syllables(w) for w in words)
    words_per_sentence = len(words) / len(sentences)
    syllables_per_word = total_syllables / len(words)

    ease = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
    grade = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59

    return round(ease, 1), round(max(grade, 0), 1)


def readability_label(ease):
    if ease is None:
        return "unknown"
    if ease >= 80:
        return "very easy"
    if ease >= 70:
        return "easy"
    if ease >= 60:
        return "standard"
    if ease >= 50:
        return "fairly difficult"
    return "difficult"


def analyze_text(text):
    """Run the full deterministic analysis. Returns a flat dict of metrics."""
    words = [w.lower() for w in RE_WORD.findall(text)]
    sentences = split_sentences(text)
    word_counts = Counter(words)
    lower_text = text.lower()

    ease, grade = flesch_scores(words, sentences)

    power_hits = sorted(w for w in POWER_WORDS if word_counts[w])
    urgency_hits = sorted(w for w in URGENCY_WORDS if word_counts[w])
    cta_hits = sorted(w for w in CTA_VERBS if word_counts[w])
    risk_hits = [p for p in RISK_REVERSAL_PHRASES if p in lower_text]

    second_person = word_counts["you"] + word_counts["your"] + word_counts["you're"]
    first_person = word_counts["i"] + word_counts["we"] + word_counts["our"] + word_counts["my"]

    specifics = {
        "money_amounts": RE_MONEY.findall(text),
        "percentages": RE_PERCENT.findall(text),
        "timeframes": RE_TIMEFRAME.findall(text),
    }
    specificity_count = sum(len(v) for v in specifics.values())

    caps_words = [w for w in re.findall(r"\b[A-Z]{2,}\b", text) if len(w) > 1]

    flags = []
    if not cta_hits:
        flags.append("No call-to-action verb detected")
    if grade is not None and grade > 9:
        flags.append(f"Reads at grade {grade} — feed copy should be under grade 7")
    if len(words) > 0 and second_person == 0:
        flags.append("Never addresses the reader ('you' appears zero times)")
    if specificity_count == 0:
        flags.append("No concrete numbers — vague claims don't convert")
    if len(words) > 400:
        flags.append(f"{len(words)} words — long even for a video script")

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_words_per_sentence": round(len(words) / len(sentences), 1) if sentences else 0,
        "flesch_reading_ease": ease,
        "flesch_kincaid_grade": grade,
        "readability": readability_label(ease),
        "power_words": power_hits,
        "urgency_words": urgency_hits,
        "cta_verbs": cta_hits,
        "risk_reversal_phrases": risk_hits,
        "second_person_count": second_person,
        "first_person_count": first_person,
        "specificity": specifics,
        "specificity_count": specificity_count,
        "all_caps_words": caps_words[:10],
        "question_count": text.count("?"),
        "flags": flags,
    }
