from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    type: str
    score: float

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: "Span") -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, other: "Span") -> bool:
        return self.start <= other.start and other.end <= self.end

    def shifted(self, offset: int) -> "Span":
        return replace(self, start=self.start + offset, end=self.end + offset)


def merge(text: str, rule_spans: list[Span], model_spans: list[Span]) -> list[Span]:
    kept = non_overlapping(sorted(rule_spans, key=lambda s: (s.start, -s.length)))
    model_parts = [part for span in unions(model_spans) for part in parts_outside(text, span, kept)]
    return sorted(kept + model_parts, key=lambda s: s.start)


def non_overlapping(spans: list[Span]) -> list[Span]:
    kept: list[Span] = []
    for span in spans:
        if not any(span.overlaps(k) for k in kept):
            kept.append(span)
    return kept


def unions(spans: list[Span]) -> list[Span]:
    merged: list[Span] = []
    for span in sorted(spans, key=lambda s: s.start):
        if merged and span.start < merged[-1].end:
            merged[-1] = union(merged[-1], span)
        else:
            merged.append(span)
    return merged


def union(a: Span, b: Span) -> Span:
    best = a if a.score >= b.score else b
    return Span(a.start, max(a.end, b.end), best.type, best.score)


def parts_outside(text: str, span: Span, others: list[Span]) -> list[Span]:
    parts = []
    position = span.start
    for other in sorted((o for o in others if o.overlaps(span)), key=lambda o: o.start):
        if position < other.start:
            parts.append(replace(span, start=position, end=other.start))
        position = max(position, other.end)
    if position < span.end:
        parts.append(replace(span, start=position))
    return [stripped for part in parts if (stripped := strip_whitespace(text, part)).length > 0]


def strip_whitespace(text: str, span: Span) -> Span:
    value = text[span.start : span.end]
    leading = len(value) - len(value.lstrip())
    trailing = len(value) - len(value.rstrip())
    return replace(span, start=span.start + leading, end=max(span.start + leading, span.end - trailing))
