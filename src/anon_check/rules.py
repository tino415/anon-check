import re
from collections.abc import Callable
from dataclasses import dataclass

from anon_check.spans import Span


@dataclass(frozen=True)
class Rule:
    type: str
    pattern: re.Pattern[str]
    is_valid: Callable[[str], bool] = lambda _: True


def find_rule_spans(text: str) -> list[Span]:
    return [
        Span(*value, rule.type, 1.0)
        for rule in RULES
        for match in rule.pattern.finditer(text)
        if (value := valid_value(rule, text, match))
    ]


def valid_value(rule: Rule, text: str, match: re.Match[str]) -> tuple[int, int] | None:
    start, end = value_span(match)
    if rule.is_valid(text[start:end]):
        return start, end
    for cut in shorter_cuts(text, start, end):
        candidate = text[start:cut]
        if rule.pattern.fullmatch(candidate) and rule.is_valid(candidate):
            return start, cut
    return None


def shorter_cuts(text: str, start: int, end: int) -> list[int]:
    return [i for i in range(end - 1, start, -1) if text[i] in " -"]


def value_span(match: re.Match[str]) -> tuple[int, int]:
    return match.span("v") if match.groupdict().get("v") else match.span()


def digits(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def is_valid_iban(value: str) -> bool:
    compact = value.replace(" ", "")
    rearranged = compact[4:] + compact[:4]
    return int("".join(str(int(c, 36)) for c in rearranged)) % 97 == 1


def is_valid_rodne_cislo(value: str) -> bool:
    number = digits(value)
    month = int(number[2:4])
    day = int(number[4:6])
    if month not in RODNE_CISLO_MONTHS or day not in range(1, 32):
        return False
    if len(number) == 9:
        return "/" in value and int(number[:2]) < 54
    return int(number) % 11 == 0 or (int(number[:9]) % 11 == 10 and number[9] == "0")


def is_valid_ico(value: str) -> bool:
    weighted = sum(int(d) * (8 - i) for i, d in enumerate(value[:7]))
    remainder = weighted % 11
    check = {0: 1, 1: 0}.get(remainder, 11 - remainder)
    return check % 10 == int(value[7])


def is_valid_card(value: str) -> bool:
    reversed_digits = [int(c) for c in digits(value)][::-1]
    doubled = [d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(reversed_digits)]
    return sum(doubled) % 10 == 0


RODNE_CISLO_MONTHS = {*range(1, 13), *range(21, 33), *range(51, 63), *range(71, 83)}

OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"

RULES = [
    Rule("EMAIL", re.compile(r"[\w.%+-]+@[\w-]+(?:\.[\w-]+)*\.[^\W\d_]{2,}")),
    Rule("PHONE", re.compile(r"(?:\+|\b00)42[01](?:[ ]?\d){9}\b")),
    Rule("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b"), is_valid_iban),
    Rule("RODNE_CISLO", re.compile(r"\b\d{6}/?\d{3,4}\b"), is_valid_rodne_cislo),
    Rule("DIC", re.compile(r"\b(?:SK|CZ)\d{8,10}\b|DIČ\s*:?\s*(?P<v>\d{8,10})\b", re.IGNORECASE)),
    Rule("ICO", re.compile(r"\b\d{8}\b"), is_valid_ico),
    Rule("CARD", re.compile(r"\b\d(?:[ -]?\d){12,18}\b"), is_valid_card),
    Rule("IP", re.compile(rf"\b{OCTET}(?:\.{OCTET}){{3}}\b")),
]
