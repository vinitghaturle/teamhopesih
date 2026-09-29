"use client";

import { GapResultItem } from "@/lib/types";

interface GapCheckViewProps {
  gapResults: GapResultItem[];
}

export default function GapCheckView({ gapResults }: GapCheckViewProps) {
  if (gapResults.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-lg border border-slate-800 text-slate-400">
        No testing parameter data available for spec-gap analysis.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Disclaimer Banner */}
      <div className="p-3.5 bg-blue-950/40 border border-blue-800/80 rounded-lg flex items-center justify-between text-xs text-blue-200">
        <div className="flex items-center gap-2">
          <span>ℹ️</span>
          <span>
            <strong>Notice:</strong> Spec-Gap analysis measures <em>topic coverage, not a compliance score</em>. It checks if key testing parameters from the BIS standard are mentioned in the tender specification.
          </span>
        </div>
      </div>

      {/* Gap Results Per Standard */}
      <div className="space-y-6">
        {gapResults.map((gap) => (
          <div
            key={gap.standard_number}
            className="border border-slate-800 rounded-lg bg-slate-900/70 p-5 space-y-4"
          >
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div>
                <h4 className="text-base font-bold font-mono text-blue-400">
                  {gap.standard_number}
                </h4>
                <p className="text-xs text-slate-400">
                  Total Key Parameters: <strong className="text-slate-200">{gap.total_count}</strong> | 
                  Mentioned in Tender: <strong className="text-emerald-400">{gap.matched_count}</strong> | 
                  Missing: <strong className="text-rose-400">{gap.missing_count}</strong>
                  {gap.negated_count > 0 && (
                    <span className="text-amber-400 ml-2">
                      | Negated/Needs Review: <strong>{gap.negated_count}</strong>
                    </span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-200">
                  Coverage: {gap.coverage_ratio} ({gap.total_count > 0 ? Math.round((gap.matched_count / gap.total_count) * 100) : 0}%)
                </span>
              </div>
            </div>

            {/* Parameters Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 uppercase font-semibold">
                  <tr>
                    <th className="px-3 py-2.5">Testing Parameter Topic</th>
                    <th className="px-3 py-2.5">Status</th>
                    <th className="px-3 py-2.5">Evidence Snippet in Tender Text</th>
                    <th className="px-3 py-2.5">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 bg-slate-900/40 text-slate-200">
                  {gap.parameter_checks.map((check, i) => {
                    let badgeStyle = "bg-slate-800 text-slate-400 border-slate-700";
                    let label = "NOT MENTIONED";

                    if (check.status === "mentioned") {
                      badgeStyle = "bg-emerald-950/80 text-emerald-300 border-emerald-800";
                      label = "MENTIONED";
                    } else if (check.status === "negated_needs_review") {
                      badgeStyle = "bg-amber-950/80 text-amber-300 border-amber-800";
                      label = "NEGATED / REVIEW";
                    }

                    return (
                      <tr key={i} className="hover:bg-slate-850/50 transition-colors">
                        <td className="px-3 py-3 font-medium text-slate-200">
                          {check.parameter_name}
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${badgeStyle}`}
                          >
                            {label}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-slate-300 font-mono text-[11px] max-w-md">
                          {check.evidence_snippet ? (
                            <span className="bg-slate-950 p-1.5 rounded border border-slate-800 block text-slate-300">
                              {check.evidence_snippet}
                            </span>
                          ) : (
                            <span className="text-slate-500 italic">No topic mention found</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-slate-400 text-[11px]">
                          {check.action}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
