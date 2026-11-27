import argparse
import io
import re
from collections.abc import Sequence

import pytest
from recall import all_documents

from anon_check.cli import parse_arguments, run
from anon_check.models import Model
from anon_check.spans import Span

SAMPLE = "Ján Novák, r. č. 850101/1233, IBAN SK31 1200 0000 1987 4263 7541"
SAMPLE_CSV = "Meno;IBAN\nJán Novák;SK31 1200 0000 1987 4263 7541\n"


class NameListModel:
    def __init__(self, *names: str):
        self.names = names
        self.inputs: list[str] = []

    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        self.inputs.extend(texts)
        return [
            [Span(m.start(), m.end(), "PERSON", 0.9) for name in self.names for m in re.finditer(re.escape(name), text)]
            for text in texts
        ]


@pytest.fixture
def eval_outputs() -> list[tuple[str, list[tuple[str, str]]]]:
    return [
        (anon_check(text, *format_flag, *(["--csv"] if is_csv else []), model=persons_of(expected))[1], expected)
        for text, expected, is_csv in all_documents()
        for format_flag in ([], ["--json"])
    ]


def persons_of(expected: list[tuple[str, str]]) -> NameListModel:
    return NameListModel(*(value for type, value in expected if type == "PERSON"))


def anon_check(stdin: str, *argv: str, model: Model | None = None) -> tuple[int, str]:
    out = io.StringIO()
    args: argparse.Namespace = parse_arguments(list(argv))
    status = run(args, stdin, model or NameListModel("Ján Novák"), out)
    return status, out.getvalue()
