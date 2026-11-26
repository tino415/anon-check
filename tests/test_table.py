import json

from conftest import SAMPLE_CSV, NameListModel, anon_check


def test_csv_reports_findings_by_row_and_column():
    assert anon_check(SAMPLE_CSV, "--csv") == (1, "2:1:1 9 PERSON 0.90\n2:2:1 29 IBAN 1.00\n")


def test_csv_json_adds_the_header_name():
    _, out = anon_check(SAMPLE_CSV, "--csv", "--json")
    assert [(f["row"], f["column"], f["header"], f["type"]) for f in json.loads(out)] == [
        (2, 1, "Meno", "PERSON"),
        (2, 2, "IBAN", "IBAN"),
    ]


def test_csv_json_prints_no_header_that_has_a_finding():
    text = "Ján Novák;IBAN\n850101/1233;nič\n"
    status, out = anon_check(text, "--csv", "--json")
    assert status == 1
    assert [(f["row"], f["column"], f["header"], f["type"]) for f in json.loads(out)] == [
        (1, 1, None, "PERSON"),
        (2, 1, None, "RODNE_CISLO"),
    ]


def test_csv_mask_keeps_the_header_and_masks_the_cells():
    assert anon_check(SAMPLE_CSV, "--csv", "--mask") == (0, "Meno;IBAN\nPERSON_1;IBAN_1\n")


def test_csv_with_commas_is_read_from_the_header_row():
    text = "Meno,IBAN\nJán Novák,SK31 1200 0000 1987 4263 7541\n"
    assert anon_check(text, "--csv", "--mask") == (0, "Meno,IBAN\nPERSON_1,IBAN_1\n")


def test_delimiter_overrides_the_header_row():
    text = "Meno;Poznámka, voľná\nJán Novák;nič\n"
    assert anon_check(text, "--csv", "--delimiter", ";") == (1, "2:1:1 9 PERSON 0.90\n")


def test_csv_mask_keeps_rows_columns_and_quoting():
    text = 'Meno;Poznámka\nJán Novák;"riadok;s bodkočiarkou"\nEva;\n'
    status, out = anon_check(text, "--csv", "--mask")
    assert (status, out) == (0, 'Meno;Poznámka\nPERSON_1;"riadok;s bodkočiarkou"\nEva;\n')


def test_one_value_gets_one_token_across_the_file():
    text = "Meno;Zástupca\nJán Novák;Eva Malá\nEva Malá;Ján Novák\n"
    model = NameListModel("Ján Novák", "Eva Malá")
    assert anon_check(text, "--csv", "--mask", model=model) == (
        0,
        "Meno;Zástupca\nPERSON_1;PERSON_2\nPERSON_2;PERSON_1\n",
    )


def test_the_model_reads_each_cell_with_its_header_and_header_cells_alone():
    model = NameListModel("Ján Novák")
    anon_check(SAMPLE_CSV, "--csv", model=model)
    assert model.inputs[:4] == ["Meno", "IBAN", "Meno: Ján Novák", "IBAN: SK31 1200 0000 1987 4263 7541"]


def test_a_finding_counts_only_inside_the_cell():
    model = NameListModel("Meno")
    assert anon_check("Meno;IBAN\nnič;nič\n", "--csv", model=model) == (1, "1:1:1 4 PERSON 0.90\n")


def test_a_finding_crossing_into_the_cell_is_cut_at_the_cell_start():
    model = NameListModel("Meno: Ján")
    assert anon_check("Meno\nJán Novák\n", "--csv", model=model) == (1, "2:1:1 3 PERSON 0.90\n")
