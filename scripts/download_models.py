"""Model Download Utility for Offline / Air-Gapped Operation.

Pre-downloads and caches:
1. Dense Bi-Encoder: BAAI/bge-small-en-v1.5
2. Cross-Encoder Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2
"""

import sys
import os

def download_all_models():
    print("=" * 60)
    print("  Tender Guard — Model Download Utility")
    print("=" * 60)

    try:
        from sentence_transformers import SentenceTransformer, CrossEncoder
    except ImportError:
        print("Error: sentence-transformers is not installed.")
        sys.exit(1)

    print("\n[1/2] Downloading dense bi-encoder model: 'BAAI/bge-small-en-v1.5' ...")
    embed_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    print("  ✓ Bi-Encoder cached successfully.")

    print("\n[2/2] Downloading cross-encoder model: 'cross-encoder/ms-marco-MiniLM-L-6-v2' ...")
    rerank_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    print("  ✓ Cross-Encoder cached successfully.")

    print("\n" + "=" * 60)
    print("  ALL NEURAL MODELS ARE DOWNLOADED AND READY FOR OFFLINE USE")
    print("=" * 60)


if __name__ == "__main__":
    download_all_models()
