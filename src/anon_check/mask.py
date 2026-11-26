from collections import Counter

from anon_check.spans import Span


class Masker:
    def __init__(self):
        self.tokens: dict[tuple[str, str], str] = {}
        self.count_by_type: Counter[str] = Counter()

    def token_for(self, type: str, value: str) -> str:
        key = (type, value)
        if key not in self.tokens:
            self.count_by_type[type] += 1
            self.tokens[key] = f"{type}_{self.count_by_type[type]}"
        return self.tokens[key]

    def mask(self, text: str, spans: list[Span]) -> tuple[str, list[Span]]:
        parts = []
        token_spans = []
        position = 0
        length = 0
        for span in sorted(spans, key=lambda s: s.start):
            token = self.token_for(span.type, text[span.start : span.end])
            parts.append(text[position : span.start])
            length += span.start - position
            token_spans.append(Span(length, length + len(token), span.type, 1.0))
            parts.append(token)
            length += len(token)
            position = span.end
        parts.append(text[position:])
        return "".join(parts), token_spans


def outside_tokens(spans: list[Span], token_spans: list[Span]) -> list[Span]:
    return [span for span in spans if not any(span.overlaps(token) for token in token_spans)]
