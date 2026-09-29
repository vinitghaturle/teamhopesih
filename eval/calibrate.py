"""Diagnostic script for score calibration."""

import json
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent / "app" / "backend"
sys.path.insert(0, str(BASE_DIR))

from services.retrieval.pipeline import RetrievalPipeline
from services.multilingual import translate_procurement_query


def run_diagnostics():
    p = RetrievalPipeline(use_neural=True)
    with open("eval/golden.json", "r", encoding="utf-8") as f:
        cases = json.load(f)

    print("=" * 110)
    print(f"{'ID':<10} | {'Type':<18} | {'Top-Sim':<8} | {'CE-Score':<9} | {'Top STD':<12} | {'Expected'}")
    print("=" * 110)

    in_sims = []
    out_sims = []
    in_ce = []
    out_ce = []

    for c in cases:
        q = c["query"]
        t_q, lang = translate_procurement_query(q)
        q_emb = p.embedder.encode_query(t_q)
        v_hits = p.vector_store.search(q_emb, top_k=3)
        top_v_sim = v_hits[0][1] if v_hits else 0.0
        top_v_std = v_hits[0][0].standard_number if v_hits else "None"
        ce_score = p.reranker.score(t_q, [v_hits[0][0].to_retrieval_text()])[0] if v_hits else -99.0

        if c["expected_status"] == "NO_CONFIDENT_MATCH":
            out_sims.append(top_v_sim)
            out_ce.append(ce_score)
        else:
            in_sims.append(top_v_sim)
            in_ce.append(ce_score)

        exp_str = ", ".join(c.get("expected_standards", [])) or "NONE"
        print(f"{c['id']:<10} | {c['type']:<18} | {top_v_sim:7.4f}  | {ce_score:8.2f}  | {top_v_std:<12} | {exp_str}")

    print("=" * 110)
    print("SCORE SEPARATION ANALYSIS:")
    print(f"  In-Corpus Similarity:   min = {min(in_sims):.4f}, max = {max(in_sims):.4f}, avg = {sum(in_sims)/len(in_sims):.4f}")
    print(f"  Out-of-Corpus Sim:      min = {min(out_sims):.4f}, max = {max(out_sims):.4f}, avg = {sum(out_sims)/len(out_sims):.4f}")
    print(f"  In-Corpus CrossEncoder: min = {min(in_ce):.2f}, max = {max(in_ce):.2f}, avg = {sum(in_ce)/len(in_ce):.2f}")
    print(f"  Out-of-Corpus CrossEnc: min = {min(out_ce):.2f}, max = {max(out_ce):.2f}, avg = {sum(out_ce)/len(out_ce):.2f}")


if __name__ == "__main__":
    run_diagnostics()
