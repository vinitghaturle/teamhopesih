"""Local BM25 with identical technical tokenization for documents and queries.
"""

import re
import unicodedata
from rank_bm25 import BM25Okapi

DEFAULT_RETRIEVAL_K = 10


def clean_text(text: str) -> str:
    """Normalize extraction noise without losing units, punctuation or negations."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00ad", "").replace("\u200b", "").replace("\ufeff", "")
    text = "".join(c for c in text if not unicodedata.category(c).startswith("C") or c.isspace())
    return re.sub(r"\s+", " ", text).strip()


STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "for", "in", "to", "with", "on", "at",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "this", "that",
    "these", "those", "shall", "per", "such", "including", "supply", "procurement",
    "tender", "specification", "specifications", "work", "works", "project",
    "distribution", "hiring", "general", "office", "services", "requirement",
    "requirements", "item", "items", "conforming"
}


def tokenize(text: str) -> list[str]:
    text = clean_text(text).casefold()
    # Align 11kV with 11 kV, and retain IP65, PVC, LED, Fe500, HDPE and decimal quantities.
    text = re.sub(r"(?<=\d)(?=(?:kv|kva|kw|hz|mm|mpa|v|a|w|m|g)\b)", " ", text)
    raw_tokens = re.findall(r"\d+(?:\.\d+)?|[^\W\d_]+\d*", text)
    quantities = [raw_tokens[i] + raw_tokens[i + 1] for i in range(len(raw_tokens) - 1)
                  if re.fullmatch(r"\d+(?:\.\d+)?", raw_tokens[i])
                  and raw_tokens[i + 1] in {"kv", "v", "kva", "kw", "w", "a", "hz", "mm", "mpa", "m", "g"}]
    tokens = [t for t in raw_tokens if t not in STOPWORDS and len(t) > 1]
    return tokens + quantities


class BM25Store:
    def __init__(self, documents):
        self.documents = list(documents)
        # Check standard_id uniqueness
        doc_ids = [getattr(d, "standard_id", getattr(d, "id", None)) for d in self.documents]
        if len(set(doc_ids)) != len(self.documents):
            raise ValueError("Duplicate standard IDs in BM25 corpus")
        
        corpus = []
        for d in self.documents:
            retrieval_text = d.to_retrieval_text() if hasattr(d, "to_retrieval_text") else str(d)
            corpus.append(tokenize(retrieval_text))
            
        self.token_sets = [set(tokens) for tokens in corpus]
        self.index = BM25Okapi(corpus) if corpus and any(corpus) else None

    def search(self, query: str, top_k: int = DEFAULT_RETRIEVAL_K):
        if top_k < 1:
            raise ValueError("top_k must be positive")
        tokens = tokenize(query)
        if self.index is None or not tokens:
            return []
        scores = self.index.get_scores(tokens)
        # Do not contribute arbitrary zero-overlap documents to RRF. Retain
        # matching documents even when Okapi IDF is zero/negative in tiny corpora.
        matches = [(doc, float(scores[i])) for i, doc in enumerate(self.documents)
                   if self.token_sets[i].intersection(tokens)]
        return sorted(matches, key=lambda item: (-item[1], getattr(item[0], "standard_id", getattr(item[0], "id", ""))))[:top_k]
