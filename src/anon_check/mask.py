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
        masked = ""
        token_spans = []
        position = 0
        for span in sorted(spans, key=lambda s: s.start):
            token = self.token_for(span.type, text[span.start : span.end])
            masked += text[position : span.start]
            token_spans.append(Span(len(masked), len(masked) + len(token), span.type, 1.0))
            masked += token
            position = span.end
        return masked + text[position:], token_spans


def outside_tokens(spans: list[Span], token_spans: list[Span]) -> list[Span]:
    return [span for span in spans if not any(token.contains(span) for token in token_spans)]
