"""Probability that a sentence contains sexual material.

Uses a Hugging Face text-classification pipeline backed by
`eliasalbouzidi/distilbert-nsfw-text-classifier`, a DistilBERT fine-tuned on
~190k safe/NSFW examples. The model and tokenizer are downloaded on first use
and cached locally (and in memory for the lifetime of the process).
"""

from importlib.util import find_spec

DEFAULT_MODEL = "eliasalbouzidi/distilbert-nsfw-text-classifier"

# DistilBERT's positional-embedding window; inputs longer than this must be
# truncated or the model raises a tensor-size mismatch.
MAX_TOKENS = 512

# Labels that count as "contains sexual material". The default model emits
# "nsfw"; recognized synonyms make the matcher robust to swapped checkpoints.
_POSITIVE_LABELS = {"nsfw", "sexual", "porn", "inappropriate", "sex", "explicit"}


def _require_transformers():
    if find_spec("transformers") is None or find_spec("torch") is None:
        raise RuntimeError(
            "The 'transformers' and 'torch' packages are required for "
            "sexual_content_probability(). Install them with:\n"
            "    uv add 'transformers[torch]'"
        )


class _Pipeline:
    def __init__(self, model: str):
        _require_transformers()
        from transformers import pipeline

        self._pipe = pipeline("text-classification", model=model, top_k=None)
        self._max_length = min(self._pipe.tokenizer.model_max_length, MAX_TOKENS)

    def classify(self, sentences):
        return self._pipe(sentences, truncation=True, max_length=self._max_length)


_CACHE = {}


def _pipeline(model: str):
    if model not in _CACHE:
        _CACHE[model] = _Pipeline(model)
    return _CACHE[model]


def _label_is_positive(label: str) -> bool:
    normalized = label.lower().replace(" ", "_").strip()
    return normalized in _POSITIVE_LABELS


def _positive_probability(output):
    """Extract the probability of the positive class from pipeline output."""
    for row in output:
        if row["label"].lower().startswith("label_"):
            continue
        if _label_is_positive(row["label"]):
            return row["score"]
    candidates = [row for row in output if row["label"].lower().startswith("label_")]
    if candidates:
        return max(candidates, key=lambda row: row["score"])["score"]
    return max(output, key=lambda row: row["score"])["score"]


def sexual_content_probability(sentence: str, *, model: str = DEFAULT_MODEL) -> float:
    """Return the probability in [0, 1] that ``sentence`` contains sexual material.

    An empty or whitespace-only sentence returns 0.0. The classifier model is
    loaded lazily on first call and cached for subsequent calls.
    """
    if not isinstance(sentence, str) or not sentence.strip():
        return 0.0

    output = _pipeline(model).classify([sentence])[0]
    return _positive_probability(output)