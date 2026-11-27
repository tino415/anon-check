import re
from collections.abc import Sequence
from dataclasses import dataclass, replace

from anon_check.models import Model
from anon_check.rules import find_rule_spans
from anon_check.spans import Span, merge

CHUNK_CHARS = 800
OVERLAP_CHARS = 100
BATCH_SIZE = 32
WHITESPACE = re.compile(r"\s")


@dataclass(frozen=True)
class Cell:
    text: str
    header: str | None


@dataclass(frozen=True)
class Chunk:
    cell: int
    start: int
    text: str


def find_in_text(text: str, model: Model) -> list[Span]:
    return find_in_cells([Cell(text, None)], model)[0]


def find_in_cells(cells: Sequence[Cell], model: Model) -> list[list[Span]]:
    chunks = [Chunk(i, start, text) for i, cell in enumerate(cells) for start, text in split_into_chunks(cell.text)]
    found = find_in_batches(model, [model_input(cells[c.cell].header, c.text) for c in chunks])
    model_spans: list[list[Span]] = [[] for _ in cells]
    for chunk, spans in zip(chunks, found):
        context = len(model_input(cells[chunk.cell].header, chunk.text)) - len(chunk.text)
        model_spans[chunk.cell] += [span.shifted(chunk.start) for span in inside_cell(spans, context)]
    return [merge(cell.text, find_rule_spans(cell.text), spans) for cell, spans in zip(cells, model_spans)]


def model_input(header: str | None, text: str) -> str:
    return text if header is None else f"{header}: {text}"


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
    start = end = 0
    while end < len(text):
        start = overlap_start(text, start, end)
        end = chunk_end(text, start, end)
        chunks.append((start, text[start:end]))
    return chunks


def overlap_start(text: str, previous_start: int, previous_end: int) -> int:
    if previous_end == 0:
        return 0
    space = WHITESPACE.search(text, max(previous_start + 1, previous_end - OVERLAP_CHARS), previous_end)
    return space.end() if space else previous_end


def chunk_end(text: str, start: int, previous_end: int) -> int:
    limit = start + CHUNK_CHARS
    if limit >= len(text):
        return len(text)
    for separator in ("\n", " "):
        cut = text.rfind(separator, max(start, previous_end), limit)
        if cut > start:
            return cut + 1
    return limit
