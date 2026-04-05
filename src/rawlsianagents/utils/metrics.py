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


def _similarity_from_cross_encoder(
    model: CrossEncoder,
    initial_claim: str,
    final_claim: str,
) -> float:
    """Return similarity in [0, 1] from the model's default prediction path.

    For sentence-transformers CrossEncoder with ``num_labels == 1``, the default
    ``predict`` path applies Sigmoid and returns probabilities in [0, 1].
    We treat that value as similarity and reject other ranges explicitly.
    """

    score = float(model.predict([(initial_claim, final_claim)])[0])
    if not 0.0 <= score <= 1.0:
        raise ValueError(
            "CrossEncoder score is outside [0, 1]. "
            f"model={model.config._name_or_path!r}, num_labels={model.config.num_labels}, score={score}. "
            "Use a similarity-configured CrossEncoder or provide an explicit calibration."
        )
    return score


def compute_claim_semantic_distance(
    initial_claim: str,
    final_claim: str,
    model_name: str = DEFAULT_CROSS_ENCODER_MODEL,
) -> SemanticDistanceMetrics:
    """Compute semantic similarity and distance between initial and final claims.

    Similarity is read from the CrossEncoder default prediction output, which is
    expected to be in [0, 1] for similarity-configured models. Distance is 1 - similarity.
    """

    model = _load_cross_encoder(model_name)
    similarity = _similarity_from_cross_encoder(model, initial_claim, final_claim)
    distance = 1.0 - similarity

    return SemanticDistanceMetrics(
        model_name=model_name,
        raw_score=similarity,
        similarity=similarity,
        distance=distance,
    )
