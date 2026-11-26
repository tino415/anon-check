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

    def shifted(self, offset: int) -> "Span":
        return replace(self, start=self.start + offset, end=self.end + offset)


def merge(rule_spans: list[Span], model_spans: list[Span]) -> list[Span]:
    rules_first = sorted(rule_spans, key=lambda s: (s.start, -s.length))
    best_model_first = sorted(model_spans, key=lambda s: -s.score)
    kept: list[Span] = []
    for span in rules_first + best_model_first:
        if not any(span.overlaps(k) for k in kept):
            kept.append(span)
    return sorted(kept, key=lambda s: s.start)
