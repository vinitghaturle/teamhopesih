"use client";

import { AuditResultItem } from "@/lib/types";
import StatusBadge from "./StatusBadge";

interface CitationAuditViewProps {
  auditResults: AuditResultItem[];
  detectedCitations: string[];
  summary: string;
}

export default function CitationAuditView({
  auditResults,
  detectedCitations,
  summary,
}: CitationAuditViewProps) {
  if (auditResults.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-lg border border-slate-800 text-slate-400">
        No Indian Standard citations (e.g. "IS 456", "IS 1786") detected in the tender text.
      </div>
    );
  }

  const staleCount = auditResults.filter(
    (r) => r.status === "SUPERSEDED" || r.status === "YEAR_OUTDATED"
  ).length;

  return (
    <div className="space-y-6">
      {/* Summary Header Card */}
      <div className="p-4 rounded-lg border border-slate-800 bg-slate-900/80 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-slate-200">
            Detected Citations Audit Summary
          </h4>
          <p className="text-xs text-slate-400 mt-0.5">{summary}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs bg-slate-800 text-slate-300 px-3 py-1 rounded border border-slate-700">
            Total Detected: <strong className="text-white">{detectedCitations.length}</strong>
          </span>
          {staleCount > 0 && (
            <span className="text-xs bg-rose-950/80 text-rose-300 px-3 py-1 rounded border border-rose-800 font-bold">
              {staleCount} Stale / Superseded
            </span>
          )}
        </div>
      </div>

      {/* Audit Table */}
      <div className="overflow-x-auto border border-slate-800 rounded-lg">
        <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold">
            <tr>
              <th className="px-4 py-3">Tender Citation</th>
              <th className="px-4 py-3">Audit Status</th>
              <th className="px-4 py-3">Latest Active Standard</th>
              <th className="px-4 py-3">Active Amendments</th>
              <th className="px-4 py-3">Audit Findings & Required Officer Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-900/60 text-slate-200">
            {auditResults.map((item, idx) => {
              const isStale =
                item.status === "SUPERSEDED" || item.status === "YEAR_OUTDATED";
              const isReview = item.status === "NEEDS_REVIEW" || item.replacement_needs_review;
              const isNotInCorpus = item.status === "NOT_IN_CORPUS";

              return (
                <tr
                  key={idx}
                  className={`hover:bg-slate-850/70 transition-colors ${
                    isStale
                      ? "bg-rose-950/15"
                      : isReview
                      ? "bg-purple-950/15"
                      : isNotInCorpus
                      ? "bg-slate-950/40"
                      : ""
                  }`}
                >
                  <td className="px-4 py-3.5 font-mono font-bold text-blue-300 whitespace-nowrap">
                    {item.citation}
                  </td>
                  <td className="px-4 py-3.5 whitespace-nowrap">
                    <StatusBadge status={item.status} />
                  </td>
                  <td className="px-4 py-3.5 font-mono">
                    {item.replacement ? (
                      <span className="text-emerald-400 font-bold">
                        {item.replacement}
                      </span>
                    ) : item.latest_year ? (
                      <span className="text-slate-200">
                        {item.standard_number}:{item.latest_year}
                      </span>
                    ) : (
                      <span className="text-slate-500 italic">Cannot verify (not in corpus)</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    {item.active_amendments.length > 0 ? (
                      <span className="text-slate-300">
                        {item.active_amendments.length} amendment(s)
                      </span>
                    ) : (
                      <span className="text-slate-500 italic">None</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 space-y-1">
                    <div className="font-medium text-slate-300">{item.audit_finding}</div>
                    <div className="text-[11px] text-amber-400/90 font-medium">
                      👉 Action: {item.action_required}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
