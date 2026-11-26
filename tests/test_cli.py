import io
import json
import sys
from collections.abc import Sequence

from conftest import SAMPLE, NameListModel, anon_check

from anon_check.cli import main
from anon_check.spans import Span


def test_the_sample_exits_1_with_three_findings():
    assert anon_check(SAMPLE) == (
        1,
        "1:1 9 PERSON 0.90\n1:18 11 RODNE_CISLO 1.00\n1:36 29 IBAN 1.00\n",
    )


def test_a_document_with_no_personal_data_exits_0_with_empty_stdout():
    assert anon_check("Stretnutie je 27. 11. 2026 o 10:00 v zasadačke 3.\n") == (0, "")


def test_line_and_col_are_1_based_code_points():
    status, out = anon_check("prvý riadok\nčíslo: 850101/1233\n")
    assert (status, out) == (1, "2:8 11 RODNE_CISLO 1.00\n")


def test_json_prints_the_same_findings():
    status, out = anon_check(SAMPLE, "--json")
    assert status == 1
    assert json.loads(out) == [
        {"line": 1, "col": 1, "len": 9, "type": "PERSON", "score": 0.9},
        {"line": 1, "col": 18, "len": 11, "type": "RODNE_CISLO", "score": 1.0},
        {"line": 1, "col": 36, "len": 29, "type": "IBAN", "score": 1.0},
    ]


def test_mask_replaces_each_finding_with_a_typed_token():
    assert anon_check(SAMPLE, "--mask") == (0, "PERSON_1, r. č. RODNE_CISLO_1, IBAN IBAN_1")


def test_a_second_check_of_masked_output_exits_0():
    _, masked = anon_check(SAMPLE, "--mask")
    assert anon_check(masked) == (0, "")


def test_mask_gives_the_same_value_the_same_token():
    text = "Ján Novák a Eva Malá; Ján Novák znova"
    status, out = anon_check(text, "--mask", model=NameListModel("Ján Novák", "Eva Malá"))
    assert (status, out) == (0, "PERSON_1 a PERSON_2; PERSON_1 znova")


class LateFindingModel:
    def __init__(self):
        self.calls = 0

    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        self.calls += 1
        if self.calls == 1:
            return [[] for _ in texts]
        return [[Span(0, 2, "PERSON", 0.9)] if text.startswith("r.") else [] for text in texts]


def test_mask_prints_nothing_and_exits_1_when_its_output_still_has_findings():
    assert anon_check("r. č. 850101/1233", "--mask", model=LateFindingModel()) == (1, "")


class CrossingTokenModel(LateFindingModel):
    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        self.calls += 1
        if self.calls == 1:
            return [[Span(4, 9, "PERSON", 0.9)] for _ in texts]
        return [[Span(0, len(text), "PERSON", 0.9)] for text in texts]


def test_mask_exits_1_when_a_finding_reaches_past_a_token():
    assert anon_check("Ján Novák", "--mask", model=CrossingTokenModel()) == (1, "")


class AddressModel:
    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        return [[Span(0, 17, "ADDRESS", 0.8)] if text.startswith("Hlavná") else [] for text in texts]


def test_mask_keeps_the_part_of_a_model_finding_outside_a_rule_finding():
    status, out = anon_check("Hlavná 5 tel +421905123456 ok", "--mask", model=AddressModel())
    assert (status, out) == (0, "ADDRESS_1 PHONE_1 ok")


def test_main_skips_a_utf8_bom(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO("﻿850101/1233".encode())))
    assert main([]) == 1
    assert capsys.readouterr().out == "1:1 11 RODNE_CISLO 1.00\n"


def test_main_exits_2_on_stdin_that_is_not_utf8(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"\xff\xfe")))
    assert main([]) == 2
    assert capsys.readouterr() == ("", "anon-check: stdin is not UTF-8\n")


def test_no_expected_value_appears_in_check_output(eval_outputs):
    for out, expected in eval_outputs:
        for _, value in expected:
            assert value not in out
