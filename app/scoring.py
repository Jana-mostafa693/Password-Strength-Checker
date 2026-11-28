"""Password scoring. Pure Python: no Flask, no database, no I/O.

IMPORTANT: the Runbook does not define the scoring algorithm or thresholds.
Everything below is an IMPLEMENTATION DECISION made by the application team.

Score (0-100)
    length      2 points per character, up to 20 characters      (max 40)
    variety     10 points per character class present            (max 40)
                (lowercase, uppercase, digit, other/symbol)
    uniqueness  distinct characters, up to 16, scaled            (max 20)
    penalties   -15 for a run of 3+ identical characters
                -10 per 3-character sequence ("abc", "321", "qwe"), max -20
    caps        common password            -> score at most 10
                shorter than 8 characters  -> score at most 39
                only one character class   -> score at most 59

Classification
    0-39 Weak | 40-59 Medium | 60-79 Strong | 80-100 Very Strong

The password is only used inside analyze_password() and is never stored,
logged or returned.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

MAX_PASSWORD_LENGTH = 128

WEAK, MEDIUM, STRONG, VERY_STRONG = "Weak", "Medium", "Strong", "Very Strong"
LABELS = (WEAK, MEDIUM, STRONG, VERY_STRONG)

# Upper bounds (exclusive) for each label, see module docstring.
_THRESHOLDS = ((40, WEAK), (60, MEDIUM), (80, STRONG))

# Length buckets stored in the `stats` table instead of the real length.
LENGTH_BUCKETS = ("1-7", "8-11", "12-15", "16+")

_COMMON = frozenset(
    """password passw0rd p@ssword p@ssw0rd 123456 1234567 12345678 123456789
    1234567890 qwerty qwerty123 qwertyuiop abc123 letmein welcome admin
    administrator login iloveyou monkey dragon master sunshine princess
    football baseball shadow superman trustno1 whatever freedom hello
    hello123 secret changeme default test test123 guest 111111 000000
    123123 654321 zaq12wsx asdfghjkl zxcvbnm""".split()
)

_SEQUENCES = (
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
)


@dataclass(frozen=True)
class Analysis:
    score: int
    label: str
    length_bucket: str
    checks: List[Dict[str, object]]
    recommendations: List[str]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "label": self.label,
            "length_bucket": self.length_bucket,
            "checks": self.checks,
            "recommendations": self.recommendations,
        }


def length_bucket(length: int) -> str:
    if length < 8:
        return "1-7"
    if length < 12:
        return "8-11"
    if length < 16:
        return "12-15"
    return "16+"


def classify(score: int) -> str:
    for upper, label in _THRESHOLDS:
        if score < upper:
            return label
    return VERY_STRONG


def _is_common(lowered: str) -> bool:
    if lowered in _COMMON:
        return True
    # "password123!" -> "password"
    return lowered.rstrip("0123456789!@#$%^&*._-") in _COMMON


def _has_repeat_run(text: str) -> bool:
    return any(text[i] == text[i + 1] == text[i + 2] for i in range(len(text) - 2))


def _count_sequences(lowered: str) -> int:
    found = 0
    for i in range(len(lowered) - 2):
        window = lowered[i : i + 3]
        for seq in _SEQUENCES:
            if window in seq or window in seq[::-1]:
                found += 1
                break
    return found


def analyze_password(password: str) -> Analysis:
    """Score a password and build improvement recommendations."""
    length = len(password)
    lowered = password.lower()

    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not (c.islower() or c.isupper() or c.isdigit()) for c in password)
    classes = sum((has_lower, has_upper, has_digit, has_symbol))

    unique = len(set(password))
    common = _is_common(lowered)
    repeats = _has_repeat_run(password)
    sequences = _count_sequences(lowered)

    score = min(length, 20) * 2
    score += classes * 10
    score += round(min(unique, 16) / 16 * 20)
    if repeats:
        score -= 15
    score -= min(sequences * 10, 20)

    if common:
        score = min(score, 10)
    if length < 8:
        score = min(score, 39)
    if classes <= 1:
        score = min(score, 59)
    score = max(0, min(100, int(score)))
    label = classify(score)

    checks = [
        {"id": "length", "label": "12+ characters", "passed": length >= 12},
        {"id": "lowercase", "label": "Lowercase letter", "passed": has_lower},
        {"id": "uppercase", "label": "Uppercase letter", "passed": has_upper},
        {"id": "digit", "label": "Number", "passed": has_digit},
        {"id": "symbol", "label": "Symbol", "passed": has_symbol},
        {"id": "not_common", "label": "Not a common password", "passed": not common},
        {"id": "no_patterns", "label": "No repeats or sequences",
         "passed": not repeats and sequences == 0},
    ]

    tips: List[str] = []
    if common:
        tips.append("This password is on lists of very common passwords. Pick something unique.")
    if length < 8:
        tips.append("Use at least 8 characters; 12 or more is much better.")
    elif length < 12:
        tips.append("Make it 12 or more characters long.")
    elif length < 16 and label != VERY_STRONG:
        tips.append("Extend it to 16 or more characters for maximum strength.")
    if not has_upper:
        tips.append("Add an uppercase letter (A-Z).")
    if not has_lower:
        tips.append("Add a lowercase letter (a-z).")
    if not has_digit:
        tips.append("Add at least one number (0-9).")
    if not has_symbol:
        tips.append("Add a symbol such as ! # $ % or &.")
    if repeats:
        tips.append("Avoid repeating the same character three or more times in a row.")
    if sequences:
        tips.append("Avoid predictable sequences such as abc, 123 or qwerty.")
    if length >= 8 and unique / length < 0.6:
        tips.append("Use more different characters instead of reusing the same ones.")

    return Analysis(score, label, length_bucket(length), checks, tips)
