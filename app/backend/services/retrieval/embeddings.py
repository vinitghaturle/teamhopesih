"""SentenceTransformer Embedding Model.
"""

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False

DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


class EmbeddingModel:
    def __init__(self, model_name=DEFAULT_EMBEDDING_MODEL, device="cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        if ST_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name, device=device)
            except Exception as e:
                # Fallback to all-MiniLM-L6-v2
                try:
                    self.model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
                except Exception:
                    self.model = None
                    
        self.query_prefix = "Represent this sentence for searching relevant passages: " if model_name.startswith("BAAI/bge-") else ""

    def encode(self, texts):
        if self.model is None:
            raise RuntimeError("SentenceTransformer model is not available")
        texts = list(texts)
        return np.asarray(self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False), dtype="float32")

    def encode_query(self, query):
        return self.encode([self.query_prefix + query])
