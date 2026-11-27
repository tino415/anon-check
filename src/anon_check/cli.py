import argparse
import json
import sys
from typing import TextIO

from anon_check.detect import find_in_cells, find_in_text
from anon_check.mask import Masker, outside_tokens
from anon_check.models import Model, load_model_from_env
from anon_check.spans import Span
from anon_check.table import Position, Table, parse_table

CLEAN, FOUND, ERROR = 0, 1, 2


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    try:
        text = sys.stdin.buffer.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return fail("stdin is not UTF-8")
    try:
        return run(args, text, load_model_from_env(), sys.stdout)
    except Exception as error:
        return fail(f"failed with {type(error).__name__}")


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="anon-check", description="Report personal data in stdin by position, or mask it with typed tokens."
    )
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--mask", action="store_true", help="print stdin with each finding replaced by a token")
    parser.add_argument("--csv", action="store_true", help="read stdin as CSV with a header row")
    parser.add_argument("--delimiter", choices=[",", ";"], help="CSV delimiter, read from the header row by default")
    return parser.parse_args(argv)


def run(args: argparse.Namespace, text: str, model: Model, out: TextIO) -> int:
    if args.csv:
        return run_on_table(args, parse_table(text, args.delimiter), model, out)
    return run_on_text(args, text, model, out)


def run_on_text(args: argparse.Namespace, text: str, model: Model, out: TextIO) -> int:
    spans = find_in_text(text, model)
    if args.mask:
        return write_masked_text(text, spans, model, out)
    return report([text_finding(text, span) for span in spans], args.json, out)


def run_on_table(args: argparse.Namespace, table: Table, model: Model, out: TextIO) -> int:
    cells = table.cells()
    found = find_in_cells([cell for _, cell in cells], model)
    if args.mask:
        return write_masked_table(table, found, model, out)
    flagged_headers = {position.column for (position, _), spans in zip(cells, found) if position.row == 1 and spans}
    findings = [
        cell_finding(position, span, printable_header(position, flagged_headers))
        for (position, _), spans in zip(cells, found)
        for span in spans
    ]
    return report(findings, args.json, out)


def printable_header(position: Position, flagged_headers: set[int]) -> str | None:
    return None if position.row == 1 or position.column in flagged_headers else position.header


def write_masked_text(text: str, spans: list[Span], model: Model, out: TextIO) -> int:
    masked, token_spans = Masker().mask(text, spans)
    left = outside_tokens(find_in_text(masked, model), token_spans)
    if left:
        return fail(f"--mask output still has {len(left)} findings", FOUND)
    out.write(masked)
    return CLEAN


def write_masked_table(table: Table, found: list[list[Span]], model: Model, out: TextIO) -> int:
    masker = Masker()
    masked_cells = [masker.mask(cell.text, spans) for (_, cell), spans in zip(table.cells(), found)]
    masked = table.with_cells([text for text, _ in masked_cells]).write()
    reparsed = [cell for _, cell in parse_table(masked, table.delimiter).cells()]
    if len(reparsed) != len(masked_cells):
        return fail("--mask output does not read back as the same cells")
    rechecked = find_in_cells(reparsed, model)
    left = [span for (_, tokens), spans in zip(masked_cells, rechecked) for span in outside_tokens(spans, tokens)]
    if left:
        return fail(f"--mask output still has {len(left)} findings", FOUND)
    out.write(masked)
    return CLEAN


def text_finding(text: str, span: Span) -> dict:
    line_start = text.rfind("\n", 0, span.start) + 1
    return {
        "line": text.count("\n", 0, span.start) + 1,
        "col": span.start - line_start + 1,
        **span_fields(span),
    }


def cell_finding(position: Position, span: Span, header: str | None) -> dict:
    return {
        "row": position.row,
        "column": position.column,
        "header": header,
        "col": span.start + 1,
        **span_fields(span),
    }


def span_fields(span: Span) -> dict:
    return {"len": span.length, "type": span.type, "score": round(span.score, 2)}


def report(findings: list[dict], as_json: bool, out: TextIO) -> int:
    if as_json:
        out.write(json.dumps(findings, ensure_ascii=False) + "\n")
    else:
        out.writelines(finding_line(finding) + "\n" for finding in findings)
    return FOUND if findings else CLEAN


def finding_line(finding: dict) -> str:
    location = (
        f"{finding['row']}:{finding['column']}:{finding['col']}" if "row" in finding else f"{finding['line']}:{finding['col']}"
    )
    return f"{location} {finding['len']} {finding['type']} {finding['score']:.2f}"


def fail(message: str, code: int = ERROR) -> int:
    print(f"anon-check: {message}", file=sys.stderr)
    return code
