import csv
import io
from dataclasses import dataclass

from anon_check.detect import Cell


@dataclass(frozen=True)
class Position:
    row: int
    column: int
    header: str


@dataclass(frozen=True)
class Table:
    rows: list[list[str]]
    delimiter: str
    line_terminator: str
    ends_with_newline: bool

    def cells(self) -> list[tuple[Position, Cell]]:
        header = self.rows[0] if self.rows else []
        return [
            (Position(r + 1, c + 1, header_name(header, c)), Cell(text, None if r == 0 else header_name(header, c) or None))
            for r, row in enumerate(self.rows)
            for c, text in enumerate(row)
        ]

    def with_cells(self, texts: list[str]) -> "Table":
        remaining = iter(texts)
        rows = [[next(remaining) for _ in row] for row in self.rows]
        return Table(rows, self.delimiter, self.line_terminator, self.ends_with_newline)

    def write(self) -> str:
        out = io.StringIO()
        csv.writer(out, delimiter=self.delimiter, lineterminator=self.line_terminator).writerows(self.rows)
        written = out.getvalue()
        return written if self.ends_with_newline else written.removesuffix(self.line_terminator)


def header_name(header: list[str], column: int) -> str:
    return header[column] if column < len(header) else ""


def parse_table(text: str, delimiter: str | None) -> Table:
    delimiter = delimiter or delimiter_of(text.split("\n", 1)[0])
    rows = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
    line_terminator = "\r\n" if "\r\n" in text else "\n"
    return Table(rows, delimiter, line_terminator, text.endswith("\n"))


def delimiter_of(header_line: str) -> str:
    return ";" if header_line.count(";") > header_line.count(",") else ","
