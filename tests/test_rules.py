import pytest

from anon_check.rules import find_rule_spans


def found(text: str) -> list[tuple[str, str]]:
    return [(span.type, text[span.start : span.end]) for span in find_rule_spans(text)]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("pište na jan.novak@example.sk.", [("EMAIL", "jan.novak@example.sk")]),
        ("volajte +421 905 123 456 dnes", [("PHONE", "+421 905 123 456")]),
        ("volejte +420601234567", [("PHONE", "+420601234567")]),
        ("volajte 00421905123456", [("PHONE", "00421905123456")]),
        ("účet SK31 1200 0000 1987 4263 7541.", [("IBAN", "SK31 1200 0000 1987 4263 7541")]),
        ("účet SK3112000000198742637541", [("IBAN", "SK3112000000198742637541")]),
        ("r. č. 850101/1233", [("RODNE_CISLO", "850101/1233")]),
        ("r. č. 8501011233", [("RODNE_CISLO", "8501011233")]),
        ("r. č. 905215/1009", [("RODNE_CISLO", "905215/1009")]),
        ("r. č. 450101/123", [("RODNE_CISLO", "450101/123")]),
        ("IČO 35757442", [("ICO", "35757442")]),
        ("DIČ: 2020317068", [("DIC", "2020317068")]),
        ("IČ DPH SK2020317068", [("DIC", "SK2020317068")]),
        ("karta 4111 1111 1111 1111", [("CARD", "4111 1111 1111 1111")]),
        ("karta 4111-1111-1111-1111", [("CARD", "4111-1111-1111-1111")]),
        ("z 192.168.10.24:443", [("IP", "192.168.10.24")]),
        ("IBAN SK31 1200 0000 1987 4263 7541 EUR", [("IBAN", "SK31 1200 0000 1987 4263 7541")]),
        ("SK31 1200 0000 1987 4263 7541 2026", [("IBAN", "SK31 1200 0000 1987 4263 7541")]),
        ("karta 4111 1111 1111 1111 12 27", [("CARD", "4111 1111 1111 1111")]),
    ],
)
def test_finds(text, expected):
    assert found(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "r. č. 850101/1234",
        "r. č. 851301/1233",
        "r. č. 450101123",
        "účet SK31 1200 0000 1987 4263 7542",
        "IČO 35757443",
        "karta 4111 1111 1111 1112",
        "verzia 999.1.1.1",
        "stretnutie 27. 11. 2026 o 10:00 v zasadačke 3",
    ],
)
def test_rejects(text):
    assert found(text) == []
