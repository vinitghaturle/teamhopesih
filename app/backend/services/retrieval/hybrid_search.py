"""Reciprocal Rank Fusion (RRF) and Hybrid Search Retriever.
"""

DEFAULT_RETRIEVAL_K = 10
DEFAULT_RRF_K = 60


def reciprocal_rank_fusion(rankings, top_k=DEFAULT_RETRIEVAL_K, rrf_k=DEFAULT_RRF_K):
    """Fuse one-based ranks; raw component scores are never mixed."""
    if top_k < 1 or rrf_k < 1:
        raise ValueError("top_k and rrf_k must be positive")
    documents, scores = {}, {}
    rank_map = {}  # Track component ranks for explainability (dense_rank, bm25_rank)
    
    for rank_idx, ranking in enumerate(rankings):
        seen = set()
        for document, _ in ranking:
            doc_id = getattr(document, "standard_id", getattr(document, "id", None))
            if doc_id in seen:
                continue
            seen.add(doc_id)
            rank = len(seen)
            documents[doc_id] = document
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
            
            if doc_id not in rank_map:
                rank_map[doc_id] = {}
            if rank_idx == 0:
                rank_map[doc_id]["dense_rank"] = rank
            elif rank_idx == 1:
                rank_map[doc_id]["bm25_rank"] = rank

    ids = sorted(scores, key=lambda identifier: (-scores[identifier], identifier))[:top_k]
    return [(documents[identifier], scores[identifier], rank_map.get(identifier, {})) for identifier in ids]


class HybridRetriever:
    def __init__(self, embedder, vector_store, bm25_store, rrf_k=DEFAULT_RRF_K):
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25_store = bm25_store
        self.rrf_k = rrf_k

    def search(self, query: str, top_k: int = DEFAULT_RETRIEVAL_K):
        semantic = []
        if self.embedder is not None and self.vector_store is not None:
            try:
                semantic = self.vector_store.search(self.embedder.encode_query(query), top_k)
            except Exception as e:
                semantic = []

        lexical = self.bm25_store.search(query, top_k) if self.bm25_store is not None else []
        
        # If semantic search is unavailable (BM25-only degraded mode), use lexical directly
        if not semantic:
            return [(doc, score, {"dense_rank": None, "bm25_rank": idx + 1}) for idx, (doc, score) in enumerate(lexical[:top_k])]

        return reciprocal_rank_fusion([semantic, lexical], top_k, self.rrf_k)
