from scoring import (LABELS, MAX_PASSWORD_LENGTH, analyze_password, classify,
                     length_bucket)

# --- Required examples from the project brief -------------------------------

def test_abc_is_weak():
    assert analyze_password("abc").label == "Weak"


def test_hello_pass9_is_strong():
    assert analyze_password("Hello#Pass9").label == "Strong"


def test_random_16_char_password_is_very_strong():
    assert analyze_password("Xq7!mPz2#Lw9vTr4").label == "Very Strong"


# --- Scoring behaviour ------------------------------------------------------

def test_scores_are_bounded_and_match_label_thresholds():
    samples = ["a", "abc", "password", "Hello#Pass9", "Xq7!mPz2#Lw9vTr4",
               "x" * MAX_PASSWORD_LENGTH, "Aa1!" * 32, " ", "пароль123"]
    for pw in samples:
        result = analyze_password(pw)
        assert 0 <= result.score <= 100
        assert result.label in LABELS
        assert result.label == classify(result.score)
    assert [classify(s) for s in (0, 39, 40, 59, 60, 79, 80, 100)] == [
        "Weak", "Weak", "Medium", "Medium", "Strong", "Strong", "Very Strong", "Very Strong"]


def test_common_passwords_are_capped_as_weak_even_when_decorated():
    for pw in ("password", "Password123!", "qwerty", "iloveyou99"):
        assert analyze_password(pw).label == "Weak", pw
    # a long unique string must not be mistaken for a common password
    assert analyze_password("Xq7!mPz2#Lw9vTr4").checks[5]["passed"] is True


def test_repeats_and_sequences_lower_the_score():
    clean = analyze_password("Kd8#Lm2Qz9").score          # same length and character classes
    repeated = analyze_password("Kd8#Lmmmz9").score        # run of identical characters
    sequenced = analyze_password("Kd8#Lm123z").score       # predictable sequence
    assert repeated < clean
    assert sequenced < clean
    assert analyze_password("aaaaaaaaaaaa").label == "Weak"


def test_recommendations_are_dynamic_and_reflect_the_password():
    weak = analyze_password("abc").recommendations
    text = " ".join(weak).lower()
    assert "8 characters" in text and "uppercase" in text and "number" in text and "symbol" in text
    only_length = analyze_password("Hello#Pass9").recommendations
    assert only_length == ["Make it 12 or more characters long."]
    assert analyze_password("Xq7!mPz2#Lw9vTr4").recommendations == []
    assert weak != only_length


def test_length_bucket_boundaries():
    cases = {1: "1-7", 7: "1-7", 8: "8-11", 11: "8-11", 12: "12-15", 15: "12-15", 16: "16+", 128: "16+"}
    for length, bucket in cases.items():
        assert length_bucket(length) == bucket
    assert analyze_password("Hello#Pass9").length_bucket == "8-11"
