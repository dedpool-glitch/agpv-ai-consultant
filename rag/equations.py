"""Utilities for preserving and evaluating equation-bearing RAG chunks."""

import re


EQUATION_QUERY_TERMS = (
    "equation",
    "formula",
    "expression",
    "mathematically",
    "calculate",
    "calculation",
    "relationship between",
    "defined as",
)

_LATEX_PATTERN = re.compile(
    r"(?:\\(?:frac|sum|int|sqrt|eta|theta|alpha|beta|gamma|lambda|begin\{equation)|"
    r"\$[^$\n]+\$|\\\([^\n]+\\\)|\\\[[\s\S]+?\\\])"
)
_SYMBOL_PATTERN = re.compile(r"[∑∫√≈≤≥±×÷ηθαλβγΔ]")
_EQUALITY_PATTERN = re.compile(
    r"(?m)(?:^|\n)\s*(?:[A-Za-zηθαλβγΔ][A-Za-z0-9_{}^()\- ]{0,30})"
    r"\s*(?:=|≈|≤|≥)\s*[^\n]{1,160}"
)

def equation_intent(query):
    normalized = " ".join(str(query or "").lower().split())
    return any(term in normalized for term in EQUATION_QUERY_TERMS)


def equation_signals(text):
    """Return lightweight equation indicators without interpreting the math."""
    value = str(text or "")
    latex_count = len(_LATEX_PATTERN.findall(value))
    symbol_count = len(_SYMBOL_PATTERN.findall(value))
    equality_count = len(_EQUALITY_PATTERN.findall(value))
    count = latex_count + symbol_count + equality_count
    return {
        "has_equation": count > 0,
        "equation_signal_count": count,
        "latex_signal_count": latex_count,
        "symbol_signal_count": symbol_count,
        "equality_signal_count": equality_count,
    }


def expected_term_recall(text, expected_terms):
    terms = [str(term).strip() for term in (expected_terms or []) if str(term).strip()]
    if not terms:
        return None
    normalized = str(text or "").casefold()
    compact = re.sub(r"[\s{}]", "", normalized)
    matches = 0
    for term in terms:
        normalized_term = term.casefold()
        compact_term = re.sub(r"[\s{}]", "", normalized_term)
        if normalized_term in normalized or compact_term in compact:
            matches += 1
    return matches / len(terms)
