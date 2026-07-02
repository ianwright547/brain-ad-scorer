from analysis.text_features import count_syllables, flesch_scores, analyze_text, split_sentences


def test_syllable_counts_common_words():
    assert count_syllables("cat") == 1
    assert count_syllables("make") == 1      # trailing silent e
    assert count_syllables("free") == 1      # 'ee' ending is not silent
    assert count_syllables("little") == 2    # 'le' ending is not silent
    assert count_syllables("banana") == 3
    assert count_syllables("beautiful") == 3
    assert count_syllables("guaranteed") == 3


def test_syllable_minimum_is_one():
    assert count_syllables("rhythm") >= 1
    assert count_syllables("a") == 1


def test_flesch_simple_sentence_is_easy():
    words = ["the", "cat", "sat", "on", "the", "mat"]
    ease, grade = flesch_scores(words, ["The cat sat on the mat"])
    assert ease > 80
    assert grade == 0  # clamped at zero for trivially simple text


def test_flesch_empty_input():
    assert flesch_scores([], []) == (None, None)


def test_sentence_splitting():
    assert len(split_sentences("First. Second! Third?")) == 3
    assert split_sentences("") == []


def test_analyze_detects_copy_signals():
    copy = (
        "ATTENTION homeowners! Get 50% off your first mobile detail — "
        "guaranteed or your money back. Only 3 spots left this week. "
        "Book now, it takes 5 minutes."
    )
    m = analyze_text(copy)

    assert "guaranteed" in m["power_words"]
    assert "now" in m["urgency_words"]
    assert "book" in m["cta_verbs"]
    assert "money back" in m["risk_reversal_phrases"]
    assert "50%" in m["specificity"]["percentages"]
    assert any("minutes" in t for t in m["specificity"]["timeframes"])
    assert m["second_person_count"] >= 2
    assert "ATTENTION" in m["all_caps_words"]
    assert m["flags"] == []


def test_analyze_flags_weak_copy():
    m = analyze_text("We are a company that provides quality solutions.")
    assert "No call-to-action verb detected" in m["flags"]
    assert any("you" in f for f in m["flags"])       # never addresses the reader
    assert any("numbers" in f for f in m["flags"])   # zero specificity


def test_analyze_handles_empty_text():
    m = analyze_text("")
    assert m["word_count"] == 0
    assert m["flesch_reading_ease"] is None
