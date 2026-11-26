from collections.abc import Sequence
from dataclasses import dataclass, replace

from anon_check.models import Model
from anon_check.rules import find_rule_spans
from anon_check.spans import Span, merge

CHUNK_CHARS = 800
BATCH_SIZE = 32


@dataclass(frozen=True)
class Cell:
    text: str
    header: str | None


def find_in_text(text: str, model: Model) -> list[Span]:
    chunks = split_into_chunks(text)
    found = find_in_batches(model, [chunk for _, chunk in chunks])
    model_spans = [span.shifted(start) for (start, _), spans in zip(chunks, found) for span in spans]
    return merge(find_rule_spans(text), model_spans)


def find_in_cells(cells: Sequence[Cell], model: Model) -> list[list[Span]]:
    found = find_in_batches(model, [model_input(cell) for cell in cells])
    return [
        merge(find_rule_spans(cell.text), inside_cell(spans, context_length(cell)))
        for cell, spans in zip(cells, found)
    ]


def model_input(cell: Cell) -> str:
    return cell.text if cell.header is None else f"{cell.header}: {cell.text}"


def context_length(cell: Cell) -> int:
    return len(model_input(cell)) - len(cell.text)


def inside_cell(spans: list[Span], context: int) -> list[Span]:
    return [replace(span, start=max(span.start, context)).shifted(-context) for span in spans if span.end > context]


def find_in_batches(model: Model, texts: Sequence[str]) -> list[list[Span]]:
    return [
        spans
        for batch_start in range(0, len(texts), BATCH_SIZE)
        for spans in model.find(texts[batch_start : batch_start + BATCH_SIZE])
    ]


def split_into_chunks(text: str) -> list[tuple[int, str]]:
    chunks = []
    start = 0
    while start < len(text):
        end = chunk_end(text, start)
        chunks.append((start, text[start:end]))
        start = end
    return chunks


def chunk_end(text: str, start: int) -> int:
    limit = start + CHUNK_CHARS
    if limit >= len(text):
        return len(text)
    for separator in ("\n", " "):
        cut = text.rfind(separator, start, limit)
        if cut > start:
            return cut + 1
    return limit
