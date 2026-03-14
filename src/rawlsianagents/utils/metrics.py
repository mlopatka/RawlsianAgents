"""Additional metrics utilities for negotiation outcomes."""

from dataclasses import asdict, dataclass
from functools import lru_cache

from sentence_transformers import CrossEncoder

DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/stsb-roberta-base"


@dataclass(frozen=True)
class SemanticDistanceMetrics:
    """Cross-encoder semantic distance summary for two claim texts."""

    model_name: str
    raw_score: float
    similarity: float
    distance: float

    def to_dict(self) -> dict[str, float | str]:
        """Return a JSON-serializable representation."""

        return asdict(self)


@lru_cache(maxsize=1)
def _load_cross_encoder(model_name: str) -> CrossEncoder:
    """Cache model instances to avoid repeated loading cost."""

    return CrossEncoder(model_name)


def _normalize_stsb_score(raw_score: float) -> float:
    """Normalize STS-B style scores from [0, 5] to [0, 1]."""

    return max(0.0, min(1.0, raw_score / 5.0))


def compute_claim_semantic_distance(
    initial_claim: str,
    final_claim: str,
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
) -> SemanticDistanceMetrics:
    """Compute semantic similarity and distance between initial and final claims.

    The default model (STS-B) returns raw scores in [0, 5]. These are normalized to
    [0, 1] similarity so that distance can be represented as 1 - similarity.
    """

    model = _load_cross_encoder(model_name)
    raw_score = float(model.predict([(initial_claim, final_claim)])[0])
    similarity = _normalize_stsb_score(raw_score)
    distance = 1.0 - similarity

    return SemanticDistanceMetrics(
        model_name=model_name,
        raw_score=raw_score,
        similarity=similarity,
        distance=distance,
    )
