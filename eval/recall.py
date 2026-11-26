import os
from collections.abc import Iterator
from pathlib import Path

from anon_check.detect import find_in_cells, find_in_text
from anon_check.models import Model, load_model_from_env
from anon_check.spans import Span
from anon_check.table import parse_table

EVAL = Path(__file__).resolve().parent
LANGUAGES = ("sk", "cs", "en")


def main() -> None:
    model = load_model_from_env()
    name = os.environ.get("ANON_CHECK_MODEL", "none")
    for language in LANGUAGES:
        print(f"{name} {language} text {recall(text_results(language, model))}")
        print(f"{name} {language} csv {recall(csv_results(language, model))}")


def recall(results: list[tuple[str, bool]]) -> str:
    found = sum(covered for _, covered in results)
    return f"{found / len(results):.2f} ({found}/{len(results)})"


def text_results(language: str, model: Model) -> list[tuple[str, bool]]:
    return [
        (type, is_covered(occurrence, spans))
        for text, expected in text_documents(language)
        for spans in [find_in_text(text, model)]
        for type, value in expected
        for occurrence in occurrences(text, value)
    ]


def csv_results(language: str, model: Model) -> list[tuple[str, bool]]:
    text, expected = csv_document(language)
    cells = [cell for _, cell in parse_table(text, None).cells()]
    found = find_in_cells(cells, model)
    return [
        (type, is_covered(occurrence, spans))
        for type, value in expected
        for cell, spans in zip(cells, found)
        for occurrence in occurrences(cell.text, value)
    ]


def text_documents(language: str) -> Iterator[tuple[str, list[tuple[str, str]]]]:
    for path in sorted((EVAL / "text" / language).glob("*.txt")):
        yield path.read_text(encoding="utf-8"), expected_values(path.with_suffix(".expected"))


def csv_document(language: str) -> tuple[str, list[tuple[str, str]]]:
    path = EVAL / "csv" / f"{language}.csv"
    return path.read_text(encoding="utf-8"), expected_values(path.with_suffix(".expected"))


def all_documents() -> Iterator[tuple[str, list[tuple[str, str]], bool]]:
    for language in LANGUAGES:
        for text, expected in text_documents(language):
            yield text, expected, False
        yield *csv_document(language), True


def expected_values(path: Path) -> list[tuple[str, str]]:
    return [tuple(line.split("\t", 1)) for line in path.read_text(encoding="utf-8").splitlines() if line]


def occurrences(text: str, value: str) -> list[Span]:
    found = []
    start = text.find(value)
    while start != -1:
        found.append(Span(start, start + len(value), "EXPECTED", 1.0))
        start = text.find(value, start + 1)
    return found


def is_covered(occurrence: Span, spans: list[Span]) -> bool:
    return any(occurrence.overlaps(span) for span in spans)


if __name__ == "__main__":
    main()
