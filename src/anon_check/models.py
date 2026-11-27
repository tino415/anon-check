import os
from collections.abc import Sequence
from typing import Protocol

from anon_check.spans import Span

GLINER_LABELS = {
    "person": "PERSON",
    "address": "ADDRESS",
    "date of birth": "BIRTH_DATE",
    "phone number": "PHONE",
    "email": "EMAIL",
    "iban": "IBAN",
    "personal id number": "ID_NUMBER",
}


class Model(Protocol):
    def find(self, texts: Sequence[str]) -> list[list[Span]]: ...


class NoModel:
    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        return [[] for _ in texts]


class GlinerModel:
    def __init__(self, name: str, threshold: float):
        from gliner import GLiNER

        self.model = GLiNER.from_pretrained(name)
        self.threshold = threshold

    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        labels = list(GLINER_LABELS)
        return [
            [
                Span(e["start"], e["end"], GLINER_LABELS[e["label"]], e["score"])
                for e in self.model.predict_entities(text, labels, threshold=self.threshold)
            ]
            for text in texts
        ]


class Gliner2Model:
    def __init__(self, name: str, threshold: float):
        from gliner2 import GLiNER2

        self.model = GLiNER2.from_pretrained(name)
        self.threshold = threshold

    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        return [self.spans_in(text) for text in texts]

    def spans_in(self, text: str) -> list[Span]:
        result = self.model.extract_entities(
            text, list(GLINER_LABELS), threshold=self.threshold, include_confidence=True, include_spans=True
        )
        return [
            Span(e["start"], e["end"], GLINER_LABELS[label], e["confidence"])
            for label, entities in result["entities"].items()
            for e in entities
        ]


class TokenClassifierModel:
    def __init__(self, name: str, threshold: float):
        from transformers import pipeline

        self.pipeline = pipeline("token-classification", model=name, aggregation_strategy="simple")
        self.threshold = threshold

    def find(self, texts: Sequence[str]) -> list[list[Span]]:
        return [
            [
                Span(e["start"], e["end"], token_classifier_type(e["entity_group"]), float(e["score"]))
                for e in self.pipeline(text)
                if e["score"] >= self.threshold
            ]
            for text in texts
        ]


def token_classifier_type(entity_group: str) -> str:
    return entity_group.upper().removeprefix("PRIVATE_")


LIBRARIES = {
    "gliner": GlinerModel,
    "gliner2": Gliner2Model,
    "transformers": TokenClassifierModel,
}


def load_model_from_env() -> Model:
    library, _, name = os.environ.get("ANON_CHECK_MODEL", "none").partition(":")
    if name in ("", "none"):
        return NoModel()
    return LIBRARIES[library](name, float(os.environ.get("ANON_CHECK_THRESHOLD", "0.5")))
