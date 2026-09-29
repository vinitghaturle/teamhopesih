"""CrossEncoder Reranker.
"""

import numpy as np

try:
    from sentence_transformers import CrossEncoder
    from torch import nn
    CE_AVAILABLE = True
except ImportError:
    CE_AVAILABLE = False

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    def __init__(self, model_name=DEFAULT_RERANKER_MODEL, device="cpu"):
        self.model_name = model_name
        self.model = None
        if CE_AVAILABLE:
            try:
                self.model = CrossEncoder(model_name, device=device, activation_fn=nn.Identity())
            except Exception:
                self.model = None

    def score(self, query, documents):
        if not documents:
            return []
        if self.model is None:
            # Fallback if cross-encoder model is not loaded: return dummy flat scores
            return [0.0] * len(documents)
            
        scores = np.asarray(self.model.predict([(query, document) for document in documents], show_progress_bar=False)).reshape(-1)
        if len(scores) != len(documents) or not np.isfinite(scores).all():
            raise RuntimeError("Reranker returned invalid scores")
        return scores.tolist()
