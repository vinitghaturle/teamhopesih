"use client";

import { useState } from "react";
import { ClausePack } from "@/lib/types";
import { exportDocx, exportPdf, exportMarkdown, exportJson } from "@/lib/api";

interface ClausePackViewProps {
  clausePack: ClausePack;
  tenderTitle: string;
  requestId?: string;
}

export default function ClausePackView({ clausePack, tenderTitle, requestId }: ClausePackViewProps) {
  const [copied, setCopied] = useState(false);
  const [isExportingDocx, setIsExportingDocx] = useState(false);
  const [isExportingPdf, setIsExportingPdf] = useState(false);
  const [isExportingMd, setIsExportingMd] = useState(false);
  const [isExportingJson, setIsExportingJson] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(clausePack.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadDocx = async () => {
    try {
      setIsExportingDocx(true);
      const blob = await exportDocx(clausePack, tenderTitle, requestId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Tender_Clauses_${tenderTitle.replace(/[^a-zA-Z0-9]/g, "_")}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert("Failed to export DOCX document");
    } finally {
      setIsExportingDocx(false);
    }
  };

  const handleDownloadPdf = async () => {
    try {
      setIsExportingPdf(true);
      const blob = await exportPdf(clausePack, tenderTitle, requestId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Tender_Clauses_${tenderTitle.replace(/[^a-zA-Z0-9]/g, "_")}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert("Failed to export PDF document");
    } finally {
      setIsExportingPdf(false);
    }
  };

  const handleDownloadMd = async () => {
    try {
      setIsExportingMd(true);
      const blob = await exportMarkdown(clausePack, tenderTitle, requestId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Tender_Clauses_${tenderTitle.replace(/[^a-zA-Z0-9]/g, "_")}.md`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert("Failed to export Markdown document");
    } finally {
      setIsExportingMd(false);
    }
  };

  const handleDownloadJson = async () => {
    try {
      setIsExportingJson(true);
      const data = await exportJson(clausePack, tenderTitle, requestId);
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
      const a = document.createElement("a");
      a.href = dataStr;
      a.download = `Tender_Clauses_${tenderTitle.replace(/[^a-zA-Z0-9]/g, "_")}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert("Failed to export JSON document");
    } finally {
      setIsExportingJson(false);
    }
  };

  if (!clausePack || !clausePack.structured_clauses || clausePack.structured_clauses.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-lg border border-slate-800 text-slate-400">
        No specification clauses generated. Add or match standard requirements to produce deterministic tender clauses.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Draft Disclaimer Header */}
      <div className="p-4 bg-amber-950/40 border border-amber-800 rounded-lg flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
            <span>🛡️</span> {clausePack.header}
          </div>
          <p className="text-xs text-amber-200/90 mt-1 max-w-2xl">
            Deterministic technical clauses generated from authoritative BIS datasets (zero LLM hallucination). All clauses are draft recommendations and must be verified by the tender drafting officer before issuance.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <span>{copied ? "✓ Copied!" : "📋 Copy All"}</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadDocx}
            disabled={isExportingDocx}
            className="px-3 py-1.5 rounded bg-blue-700 hover:bg-blue-600 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <span>📄 Export DOCX</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={isExportingPdf}
            className="px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <span>📕 Export PDF</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadMd}
            disabled={isExportingMd}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <span>📝 Markdown</span>
          </button>
          <button
            type="button"
            onClick={handleDownloadJson}
            disabled={isExportingJson}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            <span>⚙️ JSON</span>
          </button>
        </div>
      </div>

      {/* Structured Clauses View */}
      <div className="space-y-6">
        {clausePack.structured_clauses.map((clause, idx) => (
          <div
            key={clause.standard_number}
            className="border border-slate-800 rounded-lg bg-slate-900/70 p-5 space-y-4"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h4 className="text-sm font-bold text-slate-100 font-mono">
                Clause #{idx + 1}: {clause.standard_number} — {clause.full_title}
              </h4>
              {clause.needs_review && (
                <span className="text-[10px] text-purple-300 bg-purple-950/80 border border-purple-800 px-2 py-0.5 rounded font-bold uppercase">
                  Verification Required
                </span>
              )}
            </div>

            {/* Section 1: Conformance Clause */}
            <div className="space-y-1">
              <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                1. Material Conformance & Quality Standards
              </h5>
              <div className="p-3 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed font-serif">
                {clause.conformance_clause}
              </div>
            </div>

            {/* Section 2: Certification Clause (if present) */}
            {clause.certification_clause && (
              <div className="space-y-1">
                <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  2. BIS Certification & Statutory Compliance
                </h5>
                <div className="p-3 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 leading-relaxed font-serif">
                  {clause.certification_clause}
                </div>
              </div>
            )}

            {/* Section 3: Allied & Testing Standards */}
            {clause.allied_clauses && clause.allied_clauses.length > 0 && (
              <div className="space-y-2">
                <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  3. Applicable Allied & Testing Standards
                </h5>
                <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-3">
                  {clause.allied_clauses.map((grp, i) => (
                    <div key={i} className="text-xs">
                      <div className="font-semibold text-blue-400 mb-1">{grp.category}:</div>
                      <ul className="list-disc list-inside space-y-1 text-slate-300">
                        {grp.standards.map((s, j) => (
                          <li key={j} className="text-[11px] leading-relaxed">
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
