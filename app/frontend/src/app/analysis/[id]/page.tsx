"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import LoadingSpinner from "@/components/LoadingSpinner";
import RequirementCard, { RequirementData } from "@/components/RequirementCard";
import {
  getTenderReview,
  getRecommendations,
  updateReviewDecision,
  exportReport,
} from "@/lib/api";

interface TenderReview {
  tender_id: number;
  title: string;
  filename: string | null;
  created_at: string | null;
  requirements: RequirementData[];
}

export default function AnalysisResultsPage() {
  const params = useParams();
  const tenderId = Number(params.id);

  const [data, setData] = useState<TenderReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [recommending, setRecommending] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRecommendations, setHasRecommendations] = useState(false);

  const loadReview = useCallback(async () => {
    try {
      const result = await getTenderReview(tenderId);
      setData(result);
      const hasRecs = result.requirements.some(
        (r: RequirementData) => r.recommendations.length > 0
      );
      setHasRecommendations(hasRecs);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [tenderId]);

  useEffect(() => {
    loadReview();
  }, [loadReview]);

  const handleGetRecommendations = async () => {
    setRecommending(true);
    setError(null);
    try {
      await getRecommendations(tenderId);
      await loadReview();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Recommendation failed");
    } finally {
      setRecommending(false);
    }
  };

  const handleDecision = async (
    recId: number,
    decision: "accept" | "reject" | "flag"
  ) => {
    try {
      await updateReviewDecision(recId, decision);
      // Update local state
      setData((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          requirements: prev.requirements.map((req) => ({
            ...req,
            recommendations: req.recommendations.map((rec) =>
              rec.id === recId ? { ...rec, decision } : rec
            ),
          })),
        };
      });
    } catch {
      console.error("Failed to update decision");
    }
  };

  const handleExport = async (format: "pdf" | "docx") => {
    setExporting(true);
    try {
      await exportReport(tenderId, format);
    } catch {
      setError("Export failed");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20">
        <LoadingSpinner message="Loading analysis results..." />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="text-4xl mb-4">😞</div>
        <p className="text-red-400 mb-4">{error}</p>
      </div>
    );
  }

  if (!data) return null;

  const totalRecs = data.requirements.reduce(
    (sum, r) => sum + r.recommendations.length,
    0
  );
  const acceptedCount = data.requirements.reduce(
    (sum, r) =>
      sum + r.recommendations.filter((rec) => rec.decision === "accept").length,
    0
  );
  const reviewedCount = data.requirements.reduce(
    (sum, r) =>
      sum + r.recommendations.filter((rec) => rec.decision !== null).length,
    0
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">
            {data.title || `Tender #${data.tender_id}`}
          </h1>
          <p className="text-slate-400 text-sm">
            {data.filename && <span>{data.filename} · </span>}
            {data.requirements.length} requirements extracted
            {hasRecommendations && ` · ${totalRecs} recommendations`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {!hasRecommendations ? (
            <button
              onClick={handleGetRecommendations}
              disabled={recommending}
              className="px-5 py-2.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-400 hover:to-orange-400 hover:shadow-lg hover:shadow-amber-500/25 transition-all disabled:opacity-50"
            >
              {recommending
                ? "⏳ Finding Standards..."
                : "🔍 Get Recommendations"}
            </button>
          ) : (
            <>
              <button
                onClick={() => handleExport("pdf")}
                disabled={exporting}
                className="px-4 py-2 rounded-xl text-sm font-medium bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-600 transition-all disabled:opacity-50"
              >
                📥 Export PDF
              </button>
              <button
                onClick={() => handleExport("docx")}
                disabled={exporting}
                className="px-4 py-2 rounded-xl text-sm font-medium bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-600 transition-all disabled:opacity-50"
              >
                📥 Export DOCX
              </button>
            </>
          )}
        </div>
      </div>

      {/* Stats */}
      {hasRecommendations && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          {[
            {
              label: "Requirements",
              value: data.requirements.length,
              color: "text-blue-400",
            },
            { label: "Recommendations", value: totalRecs, color: "text-amber-400" },
            { label: "Accepted", value: acceptedCount, color: "text-emerald-400" },
            {
              label: "Reviewed",
              value: `${reviewedCount}/${totalRecs}`,
              color: "text-purple-400",
            },
          ].map((stat) => (
            <div
              key={stat.label}
              className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4"
            >
              <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">
                {stat.label}
              </p>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Recommending Spinner */}
      {recommending && (
        <div className="mb-8 bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8">
          <LoadingSpinner message="Searching standards knowledge base and generating recommendations..." />
          <p className="text-center text-slate-500 text-xs mt-2">
            Running hybrid search (FAISS + BM25) and generating relevance justifications.
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          ❌ {error}
        </div>
      )}

      {/* Requirements + Recommendations List */}
      <div className="space-y-6">
        {data.requirements.map((req, idx) => (
          <RequirementCard
            key={req.requirement_id}
            index={idx}
            requirement={req}
            hasRecommendations={hasRecommendations}
            onDecision={handleDecision}
          />
        ))}
      </div>
    </div>
  );
}
