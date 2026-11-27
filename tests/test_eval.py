from recall import LANGUAGES, csv_results, main, text_results

from anon_check.models import NoModel


def test_the_rules_cover_every_expected_value_but_names():
    for language in LANGUAGES:
        results = text_results(language, NoModel()) + csv_results(language, NoModel())
        assert results
        assert [type for type, covered in results if not covered and type != "PERSON"] == []


def test_eval_prints_text_and_csv_recall_for_each_language(capsys):
    main()
    assert capsys.readouterr().out.splitlines() == [
        "none sk text 0.79 (11/14)",
        "none sk csv 0.67 (4/6)",
        "none cs text 0.77 (10/13)",
        "none cs csv 0.67 (4/6)",
        "none en text 0.67 (8/12)",
        "none en csv 0.67 (4/6)",
    ]
