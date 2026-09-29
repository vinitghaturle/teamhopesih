"use client";

import React from "react";

export interface RecommendationItem {
  id: number;
  standard_id: number;
  is_number: string;
  title: string;
  scope?: string;
  sector?: string;
  relevance_score: number;
  justification: string;
  decision: "accept" | "reject" | "flag" | string | null;
  officer_notes?: string | null;
}

interface RecommendationTableProps {
  recommendations: RecommendationItem[];
  onDecision: (recId: number, decision: "accept" | "reject" | "flag") => void;
}

export default function RecommendationTable({
  recommendations,
  onDecision,
}: RecommendationTableProps) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="p-6 text-center text-slate-500 text-sm">
        No candidate standards recommended for this requirement.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700/30 bg-slate-800/30">
            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-5 py-2.5">
              IS Number
            </th>
            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-5 py-2.5">
              Title
            </th>
            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-5 py-2.5 w-28">
              Score
            </th>
            <th className="text-left text-xs font-medium text-slate-400 uppercase tracking-wider px-5 py-2.5">
              Justification
            </th>
            <th className="text-center text-xs font-medium text-slate-400 uppercase tracking-wider px-5 py-2.5 w-36">
              Decision
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/20">
          {recommendations.map((rec) => (
            <tr
              key={rec.id}
              className={`transition-colors ${
                rec.decision === "accept"
                  ? "bg-emerald-500/5"
                  : rec.decision === "reject"
                  ? "bg-red-500/5 opacity-60"
                  : rec.decision === "flag"
                  ? "bg-amber-500/5"
                  : "hover:bg-slate-700/20"
              }`}
            >
              <td className="px-5 py-3">
                <span className="text-amber-400 font-mono text-sm font-medium">
                  {rec.is_number}
                </span>
              </td>
              <td className="px-5 py-3 text-slate-200 text-sm max-w-xs">
                {rec.title}
              </td>
              <td className="px-5 py-3">
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        rec.relevance_score > 0.7
                          ? "bg-emerald-400"
                          : rec.relevance_score > 0.4
                          ? "bg-amber-400"
                          : "bg-slate-400"
                      }`}
                      style={{
                        width: `${Math.min(rec.relevance_score * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-slate-400 font-mono w-10 text-right">
                    {(rec.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
              </td>
              <td className="px-5 py-3 text-slate-400 text-xs leading-relaxed max-w-sm">
                {rec.justification}
              </td>
              <td className="px-5 py-3">
                <div className="flex items-center justify-center gap-1">
                  <button
                    onClick={() => onDecision(rec.id, "accept")}
                    title="Accept"
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-all ${
                      rec.decision === "accept"
                        ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/25"
                        : "bg-slate-700/50 text-slate-400 hover:bg-emerald-500/20 hover:text-emerald-400"
                    }`}
                  >
                    ✓
                  </button>
                  <button
                    onClick={() => onDecision(rec.id, "reject")}
                    title="Reject"
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-all ${
                      rec.decision === "reject"
                        ? "bg-red-500 text-white shadow-lg shadow-red-500/25"
                        : "bg-slate-700/50 text-slate-400 hover:bg-red-500/20 hover:text-red-400"
                    }`}
                  >
                    ✗
                  </button>
                  <button
                    onClick={() => onDecision(rec.id, "flag")}
                    title="Flag for review"
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm transition-all ${
                      rec.decision === "flag"
                        ? "bg-amber-500 text-white shadow-lg shadow-amber-500/25"
                        : "bg-slate-700/50 text-slate-400 hover:bg-amber-500/20 hover:text-amber-400"
                    }`}
                  >
                    🚩
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
