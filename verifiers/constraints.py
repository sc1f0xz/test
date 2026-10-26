"""Instruction-constraint checkers written from the public IFEval-style
instruction taxonomy (Zhou et al. 2023) + Thai-aware extras.

Each checker: fn(response, **kwargs) -> bool.  check_all(response, ids, kwargs_list)
mirrors the `instruction_id_list` + `kwargs` layout used by IF-RLVR datasets
(allenai/IF_multi_constraints_*, Nemotron IF RL, Typhoon AutoIF).

Do NOT tune training data on IFEval prompts themselves — these checkers are
for training-set constraints and our own held-out checks.
"""
from __future__ import annotations

import json
import re

_THINK = re.compile(r"<think>.*?</think>", re.S)
_THAI = re.compile(r"[฀-๿]")
_LATIN = re.compile(r"[A-Za-z]")


def strip_think(text: str) -> str:
    return _THINK.sub("", text).strip()


def _words(text: str) -> list[str]:
    # Thai has no spaces between words; count Thai "words" ≈ chars/4.5 is unreliable,
    # so callers should prefer char limits for Thai. Here: whitespace tokens.
    return re.findall(r"\S+", text)


def _cmp(n: int, relation: str, target: int) -> bool:
    return {"less than": n < target, "at least": n >= target, "at most": n <= target,
            "exactly": n == target, "more than": n > target}[relation]


def number_words(r, relation, num_words, **_):
    return _cmp(len(_words(r)), relation, num_words)


def number_chars(r, relation, num_chars, **_):
    return _cmp(len(r), relation, num_chars)


def number_paragraphs(r, num_paragraphs, **_):
    paras = [p for p in re.split(r"\s?\*\*\*\s?", r) if p.strip()]
    return len(paras) == num_paragraphs


def number_bullet_lists(r, num_bullets, **_):
    return len(re.findall(r"^\s*[\*\-•]\s", r, re.M)) == num_bullets


def keywords_include(r, keywords, **_):
    return all(re.search(re.escape(k), r, re.I) for k in keywords)


def keywords_exclude(r, forbidden_words, **_):
    return not any(re.search(r"\b" + re.escape(w) + r"\b", r, re.I) for w in forbidden_words)


def keyword_frequency(r, keyword, frequency, relation, **_):
    return _cmp(len(re.findall(re.escape(keyword), r, re.I)), relation, frequency)


def letter_frequency(r, letter, let_frequency, let_relation, **_):
    return _cmp(r.lower().count(letter.lower()), let_relation, let_frequency)


def no_comma(r, **_):
    return "," not in r and "，" not in r


def all_lowercase(r, **_):
    return r == r.lower() and bool(_LATIN.search(r))


def all_uppercase(r, **_):
    return r == r.upper() and bool(_LATIN.search(r))


def capital_word_frequency(r, capital_frequency, capital_relation, **_):
    return _cmp(len(re.findall(r"\b[A-Z]{2,}\b", r)), capital_relation, capital_frequency)


def end_checker(r, end_phrase, **_):
    return r.strip().endswith(end_phrase.strip())


def startend_quotation(r, **_):
    s = r.strip()
    return len(s) >= 2 and s[0] == '"' and s[-1] == '"'


def title(r, **_):
    return bool(re.search(r"<<[^\n]+>>", r))


def placeholders(r, num_placeholders, **_):
    return len(re.findall(r"\[[^\]]+\]", r)) >= num_placeholders


def postscript(r, postscript_marker, **_):
    return bool(re.search(re.escape(postscript_marker), r))


def highlighted_sections(r, num_highlights, **_):
    return len(re.findall(r"\*[^\n\*]+\*", r)) >= num_highlights


def sections(r, section_spliter, num_sections, **_):
    parts = re.split(r"\s?" + re.escape(section_spliter) + r"\s?\d+\s?", r)
    return len(parts) - 1 >= num_sections


def json_format(r, **_):
    s = r.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.I)
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False


def response_language(r, language, **_):
    """'th' = majority of letters Thai; 'en' = majority Latin."""
    th, lat = len(_THAI.findall(r)), len(_LATIN.findall(r))
    if language == "th":
        return th > lat
    if language == "en":
        return lat > th and th == 0
    raise ValueError(f"unsupported language {language}")


def two_responses(r, **_):
    parts = [p.strip() for p in r.split("******")]
    return len(parts) == 2 and all(parts) and parts[0] != parts[1]


REGISTRY = {
    "length_constraints:number_words": number_words,
    "length_constraints:number_paragraphs": number_paragraphs,
    "detectable_format:number_bullet_lists": number_bullet_lists,
    "keywords:existence": keywords_include,
    "keywords:forbidden_words": keywords_exclude,
    "keywords:frequency": keyword_frequency,
    "keywords:letter_frequency": letter_frequency,
    "punctuation:no_comma": no_comma,
    "change_case:english_lowercase": all_lowercase,
    "change_case:english_capital": all_uppercase,
    "change_case:capital_word_frequency": capital_word_frequency,
    "startend:end_checker": end_checker,
    "startend:quotation": startend_quotation,
    "detectable_format:title": title,
    "detectable_content:number_placeholders": placeholders,
    "detectable_content:postscript": postscript,
    "detectable_format:number_highlighted_sections": highlighted_sections,
    "detectable_format:multiple_sections": sections,
    "detectable_format:json_format": json_format,
    "language:response_language": response_language,
    "combination:two_responses": two_responses,
    "length_constraints:number_chars": number_chars,  # extra (useful for Thai)
}


def check_all(response: str, instruction_ids: list[str], kwargs_list: list[dict] | None = None) -> dict:
    response = strip_think(response)
    kwargs_list = kwargs_list or [{}] * len(instruction_ids)
    results, unsupported = {}, []
    for iid, kw in zip(instruction_ids, kwargs_list):
        fn = REGISTRY.get(iid)
        if fn is None:
            unsupported.append(iid)
            continue
        kw = {k: v for k, v in (kw or {}).items() if v is not None}
        try:
            results[iid] = bool(fn(response, **kw))
        except (TypeError, KeyError, ValueError):
            unsupported.append(iid)
    return {"all_ok": bool(results) and all(results.values()) and not unsupported,
            "results": results, "unsupported": unsupported}
