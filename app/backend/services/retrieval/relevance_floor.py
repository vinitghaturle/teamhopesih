"""Post-retrieval Relevance Floor and Threshold Evaluation.

Applied to the top-1 semantic cosine similarity score and Cross-Encoder score.
If below floor, returns a fixed refusal rather than hallucinating answers.
Deterministic identifier matches (e.g. "IS 14543") are exempt from the floor.
"""

from typing import Optional, Dict, Any, List

# Calibrated on Golden Set (In-corpus min: 0.7486, Out-of-corpus max: 0.5877)
RELEVANCE_FLOOR = 0.65
CROSS_ENCODER_FLOOR = -5.0


def evaluate_relevance_floor(
    retrieved_items: List[Dict[str, Any]],
    floor: float = RELEVANCE_FLOOR,
    has_exact_identifier_match: bool = False,
    rerank_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Evaluate whether the top candidate clears the minimum relevance floor.
    
    Returns a dict with:
      - decision: 'pass' | 'exempt_identifier_match' | 'not_measurable' | 'below_floor'
      - top_similarity: float | None
      - reason: str
    """
    if has_exact_identifier_match:
        return {
            "decision": "exempt_identifier_match",
            "top_similarity": None,
            "reason": "The query explicitly names an Indian Standard matched by the deterministic resolver; semantic relevance floor is exempt.",
        }

    similarities = [
        item.get("semantic_similarity") for item in retrieved_items
        if item.get("semantic_similarity") is not None
    ]
    top_similarity = max(similarities) if similarities else None

    if top_similarity is None:
        return {
            "decision": "not_measurable",
            "top_similarity": None,
            "reason": "No dense semantic similarity was measurable (BM25-only degraded mode), floor cannot be applied directly.",
        }

    # Dual threshold check: Cosine similarity floor OR CrossEncoder refusal floor
    if top_similarity < floor or (rerank_score is not None and rerank_score < CROSS_ENCODER_FLOOR):
        return {
            "decision": "below_floor",
            "top_similarity": top_similarity,
            "reason": f"Top similarity score ({top_similarity:.3f}) is below the calibrated threshold ({floor:.2f}). No confident match in indexed BIS corpus.",
        }

    return {
        "decision": "pass",
        "top_similarity": top_similarity,
        "reason": f"Top similarity score ({top_similarity:.3f}) cleared the relevance floor ({floor:.2f}).",
    }
