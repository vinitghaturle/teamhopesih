"""Dense Vector Store with FAISS IndexFlatIP.
"""

import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

DEFAULT_RETRIEVAL_K = 10


class VectorStore:
    def __init__(self):
        self.index = None
        self.documents = []

    @staticmethod
    def _vectors(values):
        values = np.array(values, dtype="float32", order="C", copy=True)
        if values.ndim != 2 or not np.isfinite(values).all() or np.any(np.linalg.norm(values, axis=1) == 0):
            raise ValueError("Expected finite, nonzero two-dimensional vectors")
        if FAISS_AVAILABLE:
            faiss.normalize_L2(values)
        else:
            norms = np.linalg.norm(values, axis=1, keepdims=True)
            values = values / np.maximum(norms, 1e-12)
        return values

    def add(self, embeddings, documents):
        vectors = self._vectors(embeddings)
        if len(vectors) != len(documents) or not documents:
            raise ValueError("Embeddings must match a nonempty document list")
        if self.index is None:
            if FAISS_AVAILABLE:
                self.index = faiss.IndexFlatIP(vectors.shape[1])
            else:
                self.index = "numpy_fallback"
                self.vectors = []
        if FAISS_AVAILABLE and vectors.shape[1] != self.index.d:
            raise ValueError("Embedding dimension mismatch")
        
        if FAISS_AVAILABLE:
            self.index.add(vectors)
        else:
            if not hasattr(self, "vectors"):
                self.vectors = []
            self.vectors.append(vectors)
            
        self.documents.extend(documents)

    def search(self, query_embedding, top_k=DEFAULT_RETRIEVAL_K):
        if top_k < 1:
            raise ValueError("top_k must be positive")
        if self.index is None:
            return []
        query = self._vectors(query_embedding)
        
        if FAISS_AVAILABLE:
            if query.shape != (1, self.index.d):
                raise ValueError("Expected one query with the index dimension")
            scores, indices = self.index.search(query, min(top_k, len(self.documents)))
            return [(self.documents[int(i)], float(score)) for i, score in zip(indices[0], scores[0]) if i >= 0]
        else:
            # Fallback cosine calculation using numpy if FAISS native extension isn't loaded
            all_vecs = np.vstack(self.vectors)
            scores = np.dot(all_vecs, query.T).flatten()
            indices = np.argsort(-scores)[:min(top_k, len(self.documents))]
            return [(self.documents[int(i)], float(scores[i])) for i in indices]
