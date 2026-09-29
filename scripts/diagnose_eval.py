"""Diagnostic script to inspect dense, BM25, and Cross-Encoder scores for Golden and Holdout datasets."""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / "app" / "backend"
sys.path.insert(0, str(BASE_DIR))

from database import SessionLocal
from services.retrieval.pipeline import RetrievalPipeline
import numpy as np

pipeline = RetrievalPipeline(use_neural=True)


def diagnose_dataset(dataset_path: str, dataset_name: str):
    print("=" * 110)
    print(f" DIAGNOSIS RUN: {dataset_name.upper()}")
    print("=" * 110)

    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    results = []

    for case in cases:
        q_id = case["id"]
        q_type = case.get("type", "in_corpus")
        query = case["query"]
        expected_stds = case.get("expected_standards", [])
        should_refuse = case.get("should_refuse", False) or case.get("expected_status") == "NO_CONFIDENT_MATCH"

        # Direct search with full debug info
        trans_query, lang = pipeline.multilingual.translate_query(query) if hasattr(pipeline, "multilingual") else (query, "en")
        from services.multilingual import translate_procurement_query
        trans_query, lang = translate_procurement_query(query)

        # 1. BM25
        bm25_res = pipeline.bm25_store.search(trans_query, top_k=5)
        top_bm25_doc, top_bm25_score = bm25_res[0] if bm25_res else (None, 0.0)

        # 2. Dense
        q_emb_2d = pipeline.embedder.encode_query(trans_query)
        dense_res = pipeline.vector_store.search(q_emb_2d, top_k=5)
        top_dense_id, top_dense_score = dense_res[0] if dense_res else (None, 0.0)
        top_dense_doc = pipeline.doc_map.get(top_dense_id)


        # 3. Hybrid RRF Candidates
        candidates_raw = pipeline.hybrid_retriever.search(trans_query, top_k=10)
        
        # Cross Encoder scores
        docs_to_score = [c[0] for c in candidates_raw[:10]]
        texts = [d.to_retrieval_text() for d in docs_to_score]
        ce_scores = pipeline.reranker.score(trans_query, texts) if pipeline.reranker else [0.0]*len(docs_to_score)

        top_ce_idx = int(np.argmax(ce_scores)) if len(ce_scores) > 0 else 0
        top_candidate_doc = docs_to_score[top_ce_idx]
        top_ce_score = float(ce_scores[top_ce_idx])

        # Semantic sim for top CE candidate
        q_emb = pipeline.embedder.encode_query(trans_query)[0]
        d_emb = pipeline.embedder.encode([top_candidate_doc.to_retrieval_text()])[0]
        top_sem_sim = float(np.dot(q_emb, d_emb))

        results.append({
            "id": q_id,
            "type": q_type,
            "query": query,
            "trans_query": trans_query,
            "should_refuse": should_refuse,
            "expected_stds": expected_stds,
            "top_candidate": top_candidate_doc.standard_number,
            "top_candidate_title": top_candidate_doc.full_title[:40],
            "dense_score": top_sem_sim,
            "bm25_score": top_bm25_score,
            "ce_score": top_ce_score,
        })

    # Sort results by should_refuse then ce_score descending
    sorted_results = sorted(results, key=lambda x: (x["should_refuse"], -x["ce_score"]))

    print(f"{'ID':<6} | {'Refuse?':<8} | {'Top Candidate':<15} | {'Dense Cos':<10} | {'BM25':<8} | {'Cross-Enc':<10} | {'Expected':<18} | {'Title'}")
    print("-" * 110)
    for r in sorted_results:
        ref_str = "YES (Ref)" if r["should_refuse"] else "NO (Match)"
        exp_str = ", ".join(r["expected_stds"]) if r["expected_stds"] else "None"
        print(f"{r['id']:<6} | {ref_str:<8} | {r['top_candidate']:<15} | {r['dense_score']:>9.4f} | {r['bm25_score']:>7.2f} | {r['ce_score']:>9.3f} | {exp_str:<18} | {r['top_candidate_title']}")

    return sorted_results


if __name__ == "__main__":
    golden = diagnose_dataset("eval/golden.json", "Golden Dataset")
    holdout = diagnose_dataset("eval/holdout.json", "Holdout Dataset")
