"use client";

import { useState } from "react";
import Link from "next/link";
import StatusBadge from "@/components/StatusBadge";
import MatchStrengthBadge from "@/components/MatchStrengthBadge";

export default function PortalDemoPage() {
  const [department, setDepartment] = useState("National Highways & Infrastructure Development Corp");
  const [bidNumber, setBidNumber] = useState("GEM/2026/B/749210-SIM");
  const [tenderTitle, setTenderTitle] = useState("Construction of Reinforced Concrete Culverts and Rigid Pavement");
  const [category, setCategory] = useState("Civil & Road Construction");
  const [specifications, setSpecifications] = useState(
    "1. Structural concrete design and mix proportioning shall strictly follow IS 456:1978.\n" +
    "2. High strength deformed steel bars and wires for concrete reinforcement conforming to IS 1786:1985 Grade Fe 415.\n" +
    "3. Ordinary Portland Cement 43 Grade conforming to IS 8112:1989 for precast culvert elements.\n" +
    "4. Self-ballasted LED lamps for illumination conforming to safety standards."
  );

  const [isLoading, setIsLoading] = useState(false);
  const [portalResult, setPortalResult] = useState<any | null>(null);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCheckStandards = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

    try {
      const res = await fetch(`${backendUrl}/api/portal/simulate-gem-bid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bid_number: bidNumber,
          buyer_department: department,
          tender_title: tenderTitle,
          items: [
            {
              item_id: "ITEM-001",
              category_name: category,
              item_title: tenderTitle,
              quantity: 1,
              delivery_location: "New Delhi",
              raw_specifications: specifications,
            },
          ],
        }),
      });

      if (!res.ok) {
        throw new Error(`Simulation request failed: ${res.statusText}`);
      }

      const data = await res.json();
      setPortalResult(data);
      setSidePanelOpen(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to contact portal simulation endpoint.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Simulation Banner Notice */}
      <div className="bg-amber-950/80 border-b border-amber-800/80 px-4 py-2.5 text-center text-xs text-amber-200">
        <span className="font-bold">⚠️ SIMULATION & INTEGRATION DEMO ONLY:</span> This page simulates a government procurement portal form (e.g. GeM / CPPP style) embedding Tender Guard standards verification. It does <b>not</b> connect to live government servers.
      </div>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <span>🌐</span> Simulated e-Procurement Portal (GeM/CPPP Workflow Demo)
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Demonstrating automated Bureau of Indian Standards (BIS) clause verification during RFP drafting.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/embed"
              className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-700 text-blue-400 px-3 py-1.5 rounded transition-colors"
            >
              🧩 View Embed Widget Snippet
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Mock Portal Form */}
          <div className={`${sidePanelOpen ? "lg:col-span-7" : "lg:col-span-12"} space-y-6 transition-all duration-300`}>
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Draft New Tender / GeM Bid
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  Status: DRAFT
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Buyer Department</label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-400 block mb-1">Simulated Bid Reference No.</label>
                  <input
                    type="text"
                    value={bidNumber}
                    onChange={(e) => setBidNumber(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1">Tender Title</label>
                <input
                  type="text"
                  value={tenderTitle}
                  onChange={(e) => setTenderTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-1">Product / Work Category</label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs text-slate-400">Technical Specifications & Clauses</label>
                  <span className="text-[11px] text-slate-500 font-mono">Simulates buyer drafting box</span>
                </div>
                <textarea
                  rows={8}
                  value={specifications}
                  onChange={(e) => setSpecifications(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-3 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-blue-500"
                />
              </div>

              {errorMsg && (
                <div className="p-3 bg-rose-950/60 border border-rose-800 rounded text-xs text-rose-200">
                  ⚠️ {errorMsg}
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
                <span className="text-[11px] text-slate-400">
                  Tender Guard API integration plug-in
                </span>
                <div className="flex items-center gap-2">
                  {portalResult && (
                    <button
                      type="button"
                      onClick={() => setSidePanelOpen(!sidePanelOpen)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-semibold"
                    >
                      {sidePanelOpen ? "Hide Standards Panel" : "Show Standards Panel"}
                    </button>
                  )}
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={handleCheckStandards}
                    className="px-5 py-2 bg-blue-700 hover:bg-blue-600 text-white text-xs font-bold rounded shadow flex items-center gap-2 disabled:opacity-50"
                  >
                    {isLoading ? (
                      <>
                        <span className="animate-spin">⏳</span> Checking Standards...
                      </>
                    ) : (
                      <>
                        <span>🛡️</span> Check BIS Standards (Tender Guard)
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Side Drawer / Panel for Results */}
          {sidePanelOpen && portalResult && (
            <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white">
                    🛡️ Tender Guard Standards Audit
                  </span>
                  <span className="text-[10px] bg-blue-900/60 text-blue-300 border border-blue-700 px-1.5 py-0.5 rounded font-bold">
                    LIVE VERIFICATION
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setSidePanelOpen(false)}
                  className="text-slate-400 hover:text-white font-bold text-sm"
                >
                  ✕
                </button>
              </div>

              {/* Audit Summary Cards */}
              <div className="grid grid-cols-2 gap-2 text-center text-xs">
                <div className="p-2.5 bg-slate-950 rounded border border-slate-800">
                  <div className="text-slate-400 text-[11px]">Recommended BIS</div>
                  <div className="text-base font-bold font-mono text-blue-400 mt-0.5">
                    {portalResult.recommended_standards_count} Standards
                  </div>
                </div>
                <div className="p-2.5 bg-slate-950 rounded border border-slate-800">
                  <div className="text-slate-400 text-[11px]">Audit Warnings</div>
                  <div className="text-base font-bold font-mono text-rose-400 mt-0.5">
                    {portalResult.audit_findings?.length || 0} Issues
                  </div>
                </div>
              </div>

              {/* Stale Citation Warnings */}
              {portalResult.audit_findings && portalResult.audit_findings.length > 0 && (
                <div className="space-y-2">
                  <div className="text-[11px] font-bold text-rose-400 uppercase tracking-wider">
                    ⚠️ Stale Citations Detected in Draft:
                  </div>
                  {portalResult.audit_findings.map((a: any, i: number) => (
                    <div
                      key={i}
                      className="p-2.5 bg-rose-950/40 border border-rose-800 rounded text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-rose-300">
                          {a.citation} ({a.status})
                        </span>
                        {a.latest_year && (
                          <span className="text-[10px] text-slate-300 font-mono">
                            Latest: {a.standard_number}:{a.latest_year}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-300">{a.audit_finding}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Recommended Standards List */}
              <div className="space-y-2">
                <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                  Recommended Applicable Standards:
                </div>
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {portalResult.standards_summary?.map((s: any, i: number) => (
                    <div
                      key={i}
                      className="p-2.5 bg-slate-950 border border-slate-800 rounded text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-blue-400">
                          {s.standard_number}:{s.latest_year}
                        </span>
                        {s.is_compulsory_certification && (
                          <span className="text-[10px] bg-red-950 text-red-300 border border-red-800 px-1 py-0.2 rounded font-bold">
                            MANDATORY QCO
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-300">{s.full_title}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* GeM Addendum Clause Block */}
              <div className="pt-2 border-t border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                    Buyer Clause Addendum:
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(portalResult.gem_clause_block);
                      alert("Addendum clause block copied to clipboard!");
                    }}
                    className="text-[11px] text-blue-400 hover:text-blue-300 underline"
                  >
                    Copy Clause Block
                  </button>
                </div>
                <textarea
                  readOnly
                  rows={5}
                  value={portalResult.gem_clause_block}
                  className="w-full bg-slate-950 border border-slate-800 rounded p-2.5 text-[11px] font-mono text-slate-300 resize-y"
                />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
