"""Tender Guard - Golden Evaluation & Holdout Benchmark Suite.

Evaluates:
  - Top-1 Hit Rate
  - Top-3 Hit Rate
  - Multi-standard Recall@3 over FULL expected set
  - Refusal Correctness on Out-of-Corpus / Near-Miss queries
  - Score Margin between lowest accepted match and highest refused match
  - Reports Golden vs Holdout SEPARATELY. NEVER tunes on holdout.
"""

import json
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent / "app" / "backend"
sys.path.insert(0, str(BASE_DIR))

from services.retrieval.pipeline import RetrievalPipeline


def evaluate_dataset(pipeline: RetrievalPipeline, dataset_path: str, dataset_name: str):
    print("\n" + "=" * 95)
    print(f" EVALUATION RUN: {dataset_name.upper()} ({dataset_path})")
    print("=" * 95)

    with open(dataset_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    top1_hits = 0
    top3_hits = 0
    full_recall_scores = []
    refusal_correct = 0
    total_in_corpus = 0
    total_out_of_corpus = 0
    reciprocal_ranks = []
    latencies = []

    accepted_scores = []
    refused_scores = []

    print(f"{'ID':<8} | {'Type':<22} | {'Status':<18} | {'Top-1 Ret':<12} | {'Top-3 Ret':<24} | {'Recall@3':<8} | {'Verdict'}")
    print("-" * 95)

    for case in cases:
        q_id = case["id"]
        q_type = case.get("type", "in_corpus")
        query = case["query"]
        expected_stds = case.get("expected_standards", [])
        should_refuse = case.get("should_refuse", False) or case.get("expected_status") == "NO_CONFIDENT_MATCH"

        t_start = time.time()
        res = pipeline.search(query, top_k=3)
        latency = (time.time() - t_start) * 1000.0
        latencies.append(latency)

        actual_status = res["status"]
        retrieved_results = res.get("results", [])
        retrieved_std_nums = [r["standard_number"] for r in retrieved_results]
        top1_std = retrieved_std_nums[0] if retrieved_std_nums else "None"
        top3_stds_str = ", ".join(retrieved_std_nums[:3]) if retrieved_std_nums else "None"

        # Record similarity scores for margin analysis
        top_score = None
        if retrieved_results and retrieved_results[0].get("rerank_score") is not None:
            top_score = retrieved_results[0]["rerank_score"]
        elif res.get("top_candidate_score") is not None:
            top_score = res["top_candidate_score"]
        else:
            top_score = -10.0

        if actual_status == "MATCH_FOUND":
            accepted_scores.append(top_score)
        else:
            refused_scores.append(top_score)

        if should_refuse:
            total_out_of_corpus += 1
            if actual_status in ("NO_CONFIDENT_MATCH", "CLOSE_BUT_NOT_EXACT"):
                refusal_correct += 1
                verdict_str = f"[PASS - {actual_status}]"
            else:
                verdict_str = "[FAIL - HALLUCINATION]"
            rec_at_3 = 1.0 if actual_status in ("NO_CONFIDENT_MATCH", "CLOSE_BUT_NOT_EXACT") else 0.0

        else:
            total_in_corpus += 1
            # Check Top-1 and Top-3 matches
            matched_expected = set()
            for r_num in retrieved_std_nums[:3]:
                for exp in expected_stds:
                    if exp in r_num or r_num in exp:
                        matched_expected.add(exp)

            # Multi-standard recall@3 over full expected set
            rec_at_3 = len(matched_expected) / len(expected_stds) if expected_stds else 0.0
            full_recall_scores.append(rec_at_3)

            # Top-1 Hit
            top1_hit = any(exp in top1_std or top1_std in exp for exp in expected_stds)
            if top1_hit:
                top1_hits += 1
                top3_hits += 1
                reciprocal_ranks.append(1.0)
                verdict_str = "[PASS - TOP 1]"
            elif len(matched_expected) > 0:
                top3_hits += 1
                reciprocal_ranks.append(0.5)
                verdict_str = f"[PASS - {len(matched_expected)}/{len(expected_stds)} IN TOP 3]"
            else:
                reciprocal_ranks.append(0.0)
                verdict_str = "[FAIL - MISSED]"

        print(f"{q_id:<8} | {q_type:<22} | {actual_status:<18} | {top1_std:<12} | {top3_stds_str:<24} | {rec_at_3:<8.2f} | {verdict_str}")

    top1_rate = (top1_hits / total_in_corpus * 100.0) if total_in_corpus else 0.0
    top3_rate = (top3_hits / total_in_corpus * 100.0) if total_in_corpus else 0.0
    avg_recall_at_3 = (sum(full_recall_scores) / len(full_recall_scores) * 100.0) if full_recall_scores else 0.0
    refusal_rate = (refusal_correct / total_out_of_corpus * 100.0) if total_out_of_corpus else 0.0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    min_accepted = min(accepted_scores) if accepted_scores else 0.0
    max_refused = max(refused_scores) if refused_scores else -12.0
    score_margin = min_accepted - max_refused

    print("\n" + "-" * 95)
    print(f" {dataset_name.upper()} METRICS SUMMARY:")
    print(f"  • Total Test Cases:                 {len(cases)}")
    print(f"  • In-Corpus Queries:                {total_in_corpus}")
    print(f"  • Out-of-Corpus / Refusal Queries:  {total_out_of_corpus}")
    print(f"  • Top-1 Retrieval Hit Rate:         {top1_hits}/{total_in_corpus} ({top1_rate:.1f}%)")
    print(f"  • Top-3 Retrieval Hit Rate:         {top3_hits}/{total_in_corpus} ({top3_rate:.1f}%)")
    print(f"  • Full-Set Multi-Standard Recall@3: {avg_recall_at_3:.1f}%")
    print(f"  • Refusal Correctness (Zero Halluc):{refusal_correct}/{total_out_of_corpus} ({refusal_rate:.1f}%)")
    print(f"  • Mean Reciprocal Rank (MRR):       {mrr:.3f}")
    print(f"  • Score Margin (Min Acc - Max Ref): {score_margin:+.2f} (Lowest Acc: {min_accepted:.2f}, Highest Ref: {max_refused:.2f})")
    print(f"  • Average Latency per Query:        {avg_latency:.1f} ms")
    print("-" * 95)

    return {
        "dataset": dataset_name,
        "total": len(cases),
        "top1_rate": top1_rate,
        "top3_rate": top3_rate,
        "recall_at_3": avg_recall_at_3,
        "refusal_rate": refusal_rate,
        "mrr": mrr,
        "score_margin": score_margin,
        "avg_latency": avg_latency,
    }


def run_all_evaluations():
    import io
    from datetime import datetime

    output_buffer = io.StringIO()

    class DualWriter:
        def __init__(self, *writers):
            self.writers = writers
        def write(self, text):
            for w in self.writers:
                w.write(text)
        def flush(self):
            for w in self.writers:
                w.flush()

    old_stdout = sys.stdout
    sys.stdout = DualWriter(old_stdout, output_buffer)

    try:
        print("=" * 95)
        print(" TENDER GUARD — COMPREHENSIVE BENCHMARK (GOLDEN + HOLDOUT)")
        print("=" * 95)

        pipeline = RetrievalPipeline(use_neural=True)

        golden_results = evaluate_dataset(pipeline, "eval/golden.json", "Golden Dataset (Development / Calibrated)")
        
        holdout_results = None
        if Path("eval/holdout.json").exists():
            holdout_results = evaluate_dataset(pipeline, "eval/holdout.json", "Holdout Dataset (Strict Blind Validation)")

        print("\n" + "=" * 95)
        print(" OVERALL BENCHMARK COMPARISON TABLE")
        print("=" * 95)
        print(f"{'Metric':<35} | {'Golden (15 cases)':<25} | {'Holdout (9 cases)':<25}")
        print("-" * 95)
        if holdout_results:
            print(f"{'Top-1 Hit Rate':<35} | {golden_results['top1_rate']:>5.1f}%                   | {holdout_results['top1_rate']:>5.1f}%")
            print(f"{'Top-3 Hit Rate':<35} | {golden_results['top3_rate']:>5.1f}%                   | {holdout_results['top3_rate']:>5.1f}%")
            print(f"{'Multi-Standard Recall@3':<35} | {golden_results['recall_at_3']:>5.1f}%                   | {holdout_results['recall_at_3']:>5.1f}%")
            print(f"{'Refusal Correctness':<35} | {golden_results['refusal_rate']:>5.1f}%                   | {holdout_results['refusal_rate']:>5.1f}%")
            print(f"{'MRR':<35} | {golden_results['mrr']:>5.3f}                    | {holdout_results['mrr']:>5.3f}")
            print(f"{'Score Margin':<35} | {golden_results['score_margin']:>+6.2f} pts                 | {holdout_results['score_margin']:>+6.2f} pts")
        print("=" * 95)
    finally:
        sys.stdout = old_stdout

    # Save to eval/reports/<timestamp>.txt
    reports_dir = Path("eval/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"{ts}.txt"
    report_file.write_text(output_buffer.getvalue(), encoding="utf-8")
    print(f"\n[REPORT SAVED]: {report_file}")


if __name__ == "__main__":
    run_all_evaluations()
