"use client";

import { useState } from "react";
import { BillOfStandardItem } from "@/lib/types";
import StatusBadge from "./StatusBadge";
import AlliedStandardsTree from "./AlliedStandardsTree";
import OfficerReviewBar from "./OfficerReviewBar";

interface BillOfStandardsViewProps {
  standards: BillOfStandardItem[];
  requestId?: string;
}

export default function BillOfStandardsView({ standards, requestId }: BillOfStandardsViewProps) {
  const [selectedStd, setSelectedStd] = useState<BillOfStandardItem | null>(standards[0] || null);

  if (standards.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-lg border border-slate-800 text-slate-400">
        No confident standard matches recommended for this tender. Check the Citation Audit or Requirement tabs for close matches.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Standards List Sidebar */}
      <div className="lg:col-span-4 space-y-3">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-1">
          Recommended Standards ({standards.length})
        </h4>
        {standards.map((std) => {
          const isSelected = selectedStd?.standard_number === std.standard_number;
          return (
            <div
              key={std.standard_number}
              onClick={() => setSelectedStd(std)}
              className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                isSelected
                  ? "bg-slate-800 border-blue-600 shadow-md ring-1 ring-blue-600/50"
                  : "bg-slate-900/60 border-slate-800 hover:bg-slate-800/60 hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="font-mono font-bold text-sm text-blue-400">
                  {std.standard_number}:{std.version.latest_year}
                </div>
                <StatusBadge status={std.version.status} />
              </div>
              <div className="text-xs font-medium text-slate-200 mt-1 line-clamp-2">
                {std.full_title}
              </div>
              <div className="flex items-center gap-2 mt-2 text-[11px] text-slate-400">
                <span className="bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                  {std.product_category}
                </span>
                {std.is_compulsory_certification && (
                  <span className="text-amber-400 bg-amber-950/60 border border-amber-800/80 px-1.5 py-0.5 rounded font-semibold">
                    QCO
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Standard Detail Panel */}
      <div className="lg:col-span-8">
        {selectedStd ? (
          <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-6 space-y-6">
            {/* Header */}
            <div>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-xl font-bold text-slate-100 font-mono">
                  {selectedStd.standard_number}:{selectedStd.version.latest_year}
                </h3>
                <div className="flex items-center gap-2">
                  <StatusBadge status={selectedStd.version.status} />
                  <span className="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700 uppercase">
                    {selectedStd.standard_type}
                  </span>
                </div>
              </div>
              <h4 className="text-base text-slate-200 font-medium mt-1">
                {selectedStd.full_title}
              </h4>
              <p className="text-xs text-slate-400 mt-0.5">
                Category: <span className="text-slate-300 font-medium">{selectedStd.product_category}</span> | Sector: <span className="text-slate-300 font-medium">{selectedStd.industry}</span>
              </p>
            </div>

            {/* Officer Review Workflow Bar */}
            <OfficerReviewBar
              requestId={requestId || ""}
              standardNumber={selectedStd.standard_number}
            />

            {/* Officer Review Alert if needs_review */}
            {selectedStd.needs_review && (
              <div className="p-3.5 bg-purple-950/40 border border-purple-800 rounded-lg text-xs text-purple-200">
                <div className="font-bold flex items-center gap-1.5 mb-1 text-purple-300">
                  ⚠️ Officer Verification Required (Data Conflict Notice)
                </div>
                {selectedStd.needs_review_warning ||
                  "Our records conflict about the replacement/consolidation for this standard. Please confirm on the official BIS portal (services.bis.gov.in)."}
              </div>
            )}

            {/* Version & Amendments */}
            <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40 space-y-3">
              <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                Version & Published Amendments ({selectedStd.version.amendments_count})
              </h5>
              {selectedStd.version.amendments.length > 0 ? (
                <div className="space-y-2">
                  {selectedStd.version.amendments.map((a) => (
                    <div
                      key={a.amendment_number}
                      className="text-xs flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800"
                    >
                      <span className="font-semibold text-blue-400">
                        Amendment No. {a.amendment_number}
                      </span>
                      <span className="text-slate-400 font-mono">
                        {a.year ? `Year: ${a.year}` : "Active"}
                      </span>
                      {a.provenance?.verified ? (
                        <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-1 py-0.5 rounded">
                          Official Dataset
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-400 bg-slate-800 px-1 py-0.5 rounded">
                          Unverified
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No published amendments recorded for this active edition.</p>
              )}
            </div>

            {/* Certification / QCO Requirements */}
            <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40 space-y-2">
              <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                Certification & Quality Control Order (QCO)
              </h5>
              <div className="text-xs space-y-1">
                <div>
                  <span className="text-slate-400">Certification Scheme:</span>{" "}
                  <span className="text-slate-200 font-medium">{selectedStd.certification.scheme || "Scheme-I (ISI Mark)"}</span>
                </div>
                <div>
                  <span className="text-slate-400">Compulsory Certification:</span>{" "}
                  <span className={selectedStd.is_compulsory_certification ? "text-amber-400 font-bold" : "text-slate-300"}>
                    {selectedStd.is_compulsory_certification ? "MANDATORY (QCO Enforced)" : "Voluntary Scheme"}
                  </span>
                </div>
                {selectedStd.certification.legal_basis && (
                  <div className="p-2.5 rounded bg-slate-900 border border-slate-800 mt-2">
                    <span className="text-slate-400 block text-[11px] uppercase tracking-wider mb-0.5">
                      Statutory Order Reference:
                    </span>
                    <span className="text-slate-200 font-mono text-xs">
                      {selectedStd.certification.legal_basis}
                    </span>
                  </div>
                )}
                {!selectedStd.certification.legal_basis_verified && (
                  <div className="text-[11px] text-slate-400 italic mt-1">
                    * QCO statutory applicability to be verified by procurement officer against ministry gazette notification.
                  </div>
                )}
              </div>
            </div>

            {/* Key Testing Parameters (Names Only, Limits Omitted) */}
            {selectedStd.parameter_names && selectedStd.parameter_names.length > 0 && (
              <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40 space-y-2">
                <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                  Key Testing Parameters ({selectedStd.parameter_names.length})
                </h5>
                <div className="flex flex-wrap gap-1.5">
                  {selectedStd.parameter_names.map((param, i) => (
                    <span
                      key={i}
                      className="text-xs bg-slate-900 text-slate-300 px-2.5 py-1 rounded border border-slate-800 font-medium"
                    >
                      {param}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 1-Hop Allied Standards Graph */}
            <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40 space-y-3">
              <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                Allied Standards & Normative References (1-Hop Graph)
              </h5>
              <AlliedStandardsTree alliedStandards={selectedStd.allied_standards} />
            </div>

            {/* Referenced By Tender Requirements */}
            {selectedStd.referenced_by_requirements && selectedStd.referenced_by_requirements.length > 0 && (
              <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40 space-y-2">
                <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wide">
                  Referenced By Tender Requirements ({selectedStd.referenced_by_requirements.length})
                </h5>
                <div className="space-y-2">
                  {selectedStd.referenced_by_requirements.map((req, i) => (
                    <div key={i} className="text-xs p-2.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                      <span className="text-blue-400 font-mono font-bold mr-2">
                        Clause #{req.requirement_id}:
                      </span>
                      {req.clause_text}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400">Select a standard to view specifications.</div>
        )}
      </div>
    </div>
  );
}
