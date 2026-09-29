"use client";

import { useState } from "react";
import { analyzeTender } from "@/lib/api";
import { AnalyzeResponse, ExtractedRequirementItem } from "@/lib/types";
import BillOfStandardsView from "@/components/BillOfStandardsView";
import CitationAuditView from "@/components/CitationAuditView";
import GapCheckView from "@/components/GapCheckView";
import ClausePackView from "@/components/ClausePackView";
import StatusBadge from "@/components/StatusBadge";
import MatchStrengthBadge from "@/components/MatchStrengthBadge";
import SpeechInputButton from "@/components/SpeechInputButton";

const SAMPLE_TENDERS = [
  {
    id: "stale",
    name: "⚠️ Stale Citations Tender",
    description: "Cites IS 8112:1989, IS 456:1978, IS 1786:1985, IS 269:1989",
    text: `TENDER NOTICE - INFRASTRUCTURE CONSTRUCTION (STALE CITATIONS SPECIFICATION)
Subject: Construction of Reinforced Concrete Bridges and Approach Roads
Tender Reference No: NHAI/TECH/2026/BR-104

1. TECHNICAL SPECIFICATIONS
- Ordinary Portland Cement 43 Grade conforming to IS 8112:1989 shall be used for structural concrete elements.
- Structural concrete design and mix proportioning shall strictly follow IS 456:1978 code of practice for plain and reinforced concrete.
- For mass concrete foundation works, 33 Grade Ordinary Portland Cement conforming to IS 269:1989 may be utilized.
- High strength deformed steel bars and wires for concrete reinforcement conforming to IS 1786:1985 (Grade Fe 415).
- Industrial safety helmets for workers on site conforming to IS 2925:1984 specifications.
- Concrete sampling and compressive strength testing in accordance with standard test methods.`,
  },
  {
    id: "water",
    name: "💧 Water Supply Scheme",
    description: "Potable water, uPVC/HDPE pipes, packaged drinking water",
    text: `TENDER NOTICE - MUNICIPAL WATER SUPPLY SCHEME
Subject: Supply and Installation of Potable Water Supply Pipeline and Quality Monitoring Network
Tender Reference No: PHED/RAJ/2026/WTR-042

1. TECHNICAL SPECIFICATIONS
- Supply of unplasticized PVC (uPVC) pipes for cold water distribution mains with solvent cemented joints.
- Baseline water quality testing parameters shall comply with Indian Standards for potable drinking water quality.
- Packaged drinking water 20 litre jars for operational field staff distribution conforming to BIS packaged drinking water standards.
- Supply of High Density Polyethylene (HDPE) / Polyethylene pipes for municipal potable water supply network, PE-100 grade, working pressure PN 10.
- All supplied pipes and fittings must carry mandatory ISI mark certification.`,
  },
  {
    id: "construction",
    name: "🏗️ Civil Construction Tender",
    description: "TMT bars Fe 500D, concrete design, structural steel",
    text: `TENDER NOTICE - COMMERCIAL COMPLEX CONSTRUCTION
Subject: Civil, Structural and Finishing Works
Tender Reference No: CPWD/DEL/2026/CIV-089

1. TECHNICAL SPECIFICATIONS
- High strength deformed steel bars and wires (TMT Fe 500D) for reinforced cement concrete works.
- Ready-mixed concrete and design mix plain and reinforced concrete complying with BIS code of practice.
- Hot rolled medium and high tensile structural steel for roof trusses and structural framing.
- Hardened concrete core testing and compressive strength verification from NABL/BIS accredited laboratory.`,
  },
  {
    id: "electrical",
    name: "⚡ Electrical Works Tender",
    description: "PVC insulated copper cables, LT armoured cables, LED lighting",
    text: `TENDER NOTICE - INTERNAL & EXTERNAL ELECTRIFICATION
Subject: Electrification of Substation & Office Complex
Tender Reference No: PWD/ELECT/2026/EL-012

1. TECHNICAL SPECIFICATIONS
- PVC insulated copper cables and flexible cords for working voltages up to and including 1100 V.
- PVC insulated heavy duty electric cables for working voltages up to and including 1100 V.
- Self-ballasted LED lamps for general lighting services with safety requirements.
- Conduits for electrical installations (rigid PVC and steel conduits).`,
  },
];

export default function HomePage() {
  const [inputText, setInputText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedLang, setSelectedLang] = useState("auto");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"bill" | "audit" | "gaps" | "clauses" | "breakdown">("bill");

  const handleAnalyze = async () => {
    if (!inputText.trim() && !selectedFile) {
      setErrorMsg("Please paste tender specifications or upload a document (.pdf, .docx, .txt)");
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const data = await analyzeTender({
        text: inputText.trim() || undefined,
        file: selectedFile || undefined,
        lang: selectedLang,
      });
      setResult(data);
      setActiveTab("bill");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to analyze tender.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleClear = () => {
    setInputText("");
    setSelectedFile(null);
    setResult(null);
    setErrorMsg(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header Title Section */}
        <div className="border-b border-slate-800 pb-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">
                Tender Specification Analysis & BIS Standards Recommender
              </h2>
              <p className="text-xs text-slate-400 mt-1 max-w-3xl">
                Automated identification of applicable Indian Standards (BIS), stale-citation detection, specification topic gap analysis, and deterministic tender clause generation.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] bg-slate-900 border border-slate-800 px-3 py-1 rounded text-slate-300 font-mono">
                Corpus: 100 Authoritative Standards
              </span>
            </div>
          </div>
        </div>

        {/* Input & Form Section */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-6 space-y-6 shadow-sm">
          {/* Sample Tenders Bar */}
          <div>
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Quick Load Sample Tenders:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {SAMPLE_TENDERS.map((sample) => (
                <button
                  key={sample.id}
                  type="button"
                  onClick={() => {
                    setInputText(sample.text);
                    setSelectedFile(null);
                    setResult(null);
                  }}
                  className="p-2.5 text-left rounded bg-slate-800/80 hover:bg-slate-850 border border-slate-700/80 hover:border-blue-500 transition-all text-xs group"
                >
                  <div className="font-bold text-slate-200 group-hover:text-blue-400">
                    {sample.name}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                    {sample.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Input Controls */}
          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Paste Tender Text / Specifications (English, Hindi, Marathi):
              </label>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Language Hint:</span>
                <select
                  value={selectedLang}
                  onChange={(e) => setSelectedLang(e.target.value)}
                  className="bg-slate-950 border border-slate-700 text-xs rounded px-2.5 py-1 text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
                >
                  <option value="auto">🌐 Auto-Detect</option>
                  <option value="en">English (en)</option>
                  <option value="hi">हिन्दी (Hindi)</option>
                  <option value="mr">मराठी (Marathi)</option>
                </select>
              </div>
            </div>

            <textarea
              rows={7}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste clause specifications, requirement items, or full tender documents here (e.g., 'Supply of TMT steel bars Fe 500D conforming to IS 1786:1985...')."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-600 font-mono leading-relaxed resize-y"
            />

            {/* File Upload & Submit Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800">
              <div className="flex flex-wrap items-center gap-3">
                <label className="cursor-pointer px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs font-semibold text-slate-200 flex items-center gap-2 transition-colors">
                  <span>📎 Upload Document</span>
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
                <SpeechInputButton
                  onTranscript={(transcript) =>
                    setInputText((prev) => (prev ? `${prev} ${transcript}` : transcript))
                  }
                  language={selectedLang}
                  disabled={isLoading}
                />
                {selectedFile && (
                  <span className="text-xs text-blue-400 font-mono flex items-center gap-1.5">
                    <span>📄 {selectedFile.name}</span>
                    <button
                      type="button"
                      onClick={() => setSelectedFile(null)}
                      className="text-slate-400 hover:text-rose-400 font-bold ml-1"
                    >
                      ✕
                    </button>
                  </span>
                )}
              </div>

              <div className="flex items-center gap-3">
                {(inputText || selectedFile || result) && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="px-4 py-2 rounded text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-transparent transition-colors"
                  >
                    Clear All
                  </button>
                )}
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={isLoading}
                  className="px-6 py-2 rounded bg-blue-700 hover:bg-blue-600 text-white text-xs font-bold tracking-wide shadow transition-all disabled:opacity-50 flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <span className="inline-block animate-spin">⏳</span>
                      Analyzing Tender...
                    </>
                  ) : (
                    <>
                      <span>🔍</span> Analyze Specifications
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 bg-rose-950/60 border border-rose-800 rounded text-xs text-rose-200 font-medium">
              ⚠️ {errorMsg}
            </div>
          )}
        </div>

        {/* Analysis Results View */}
        {result && (
          <div className="space-y-6">
            {/* Top Summary Banner */}
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-lg font-bold text-white">
                    {result.tender_title || result.filename || "Tender Specification"}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Request ID: <span className="font-mono text-slate-300">{result.request_id}</span> | Detected Language: <span className="font-semibold text-blue-400 uppercase">{result.detected_language || "en"}</span> ({result.language_confidence ? Math.round(result.language_confidence * 100) : 100}% conf)
                    {result.is_translated && " • Translated to English via Procurement Glossary (150+ terms)"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {result.is_translated && (
                    <div className="bg-blue-950/80 border border-blue-800 px-3 py-1 rounded text-xs text-blue-300 font-semibold">
                      🌐 Glossary Mode Active
                    </div>
                  )}
                  {result.is_degraded_mode && (
                    <div className="bg-amber-950/80 border border-amber-800 px-3 py-1 rounded text-xs text-amber-300 font-semibold">
                      ⚠️ BM25 Degraded Mode Active
                    </div>
                  )}
                </div>
              </div>

              {/* Metric Counters */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded text-center">
                  <div className="text-xs text-slate-400">Total Clauses</div>
                  <div className="text-lg font-bold font-mono text-white mt-0.5">
                    {result.summary?.total_clauses ?? result.requirements?.length ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded text-center">
                  <div className="text-xs text-slate-400">Exact Matches</div>
                  <div className="text-lg font-bold font-mono text-emerald-400 mt-0.5">
                    {result.summary?.matched_clauses ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded text-center">
                  <div className="text-xs text-slate-400">Near-Miss / Warning</div>
                  <div className="text-lg font-bold font-mono text-orange-400 mt-0.5">
                    {result.summary?.close_matches ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded text-center">
                  <div className="text-xs text-slate-400">Unmatched</div>
                  <div className="text-lg font-bold font-mono text-slate-400 mt-0.5">
                    {result.summary?.unmatched_clauses ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded text-center">
                  <div className="text-xs text-slate-400">Stale Citations</div>
                  <div className="text-lg font-bold font-mono text-rose-400 mt-0.5">
                    {result.summary?.stale_citations_detected ?? 0}
                  </div>
                </div>
                <div className="bg-slate-950/60 border border-slate-800/80 p-3 rounded text-center">
                  <div className="text-xs text-slate-400">Bill of Standards</div>
                  <div className="text-lg font-bold font-mono text-blue-400 mt-0.5">
                    {result.bill_of_standards?.length ?? 0}
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-slate-800 gap-2 overflow-x-auto">
              <button
                type="button"
                onClick={() => setActiveTab("bill")}
                className={`px-4 py-2.5 text-xs font-bold tracking-wide uppercase border-b-2 transition-all whitespace-nowrap ${
                  activeTab === "bill"
                    ? "border-blue-500 text-blue-400 bg-slate-900/60"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
                }`}
              >
                📦 Bill of Standards ({result.bill_of_standards?.length ?? 0})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("audit")}
                className={`px-4 py-2.5 text-xs font-bold tracking-wide uppercase border-b-2 transition-all whitespace-nowrap ${
                  activeTab === "audit"
                    ? "border-blue-500 text-blue-400 bg-slate-900/60"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
                }`}
              >
                🔎 Citation Audit ({result.cited_standards_detected?.length ?? 0})
                {(result.summary?.stale_citations_detected ?? 0) > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.2 text-[10px] bg-rose-950 text-rose-300 border border-rose-800 rounded-full font-bold">
                    {result.summary?.stale_citations_detected}
                  </span>
                )}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("gaps")}
                className={`px-4 py-2.5 text-xs font-bold tracking-wide uppercase border-b-2 transition-all whitespace-nowrap ${
                  activeTab === "gaps"
                    ? "border-blue-500 text-blue-400 bg-slate-900/60"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
                }`}
              >
                📊 Spec Gap Check ({result.gap_results?.length ?? 0})
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("clauses")}
                className={`px-4 py-2.5 text-xs font-bold tracking-wide uppercase border-b-2 transition-all whitespace-nowrap ${
                  activeTab === "clauses"
                    ? "border-blue-500 text-blue-400 bg-slate-900/60"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
                }`}
              >
                📝 Clause Pack
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("breakdown")}
                className={`px-4 py-2.5 text-xs font-bold tracking-wide uppercase border-b-2 transition-all whitespace-nowrap ${
                  activeTab === "breakdown"
                    ? "border-blue-500 text-blue-400 bg-slate-900/60"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/30"
                }`}
              >
                📋 Requirements & Retrieval Trace ({result.requirements?.length ?? 0})
              </button>
            </div>

            {/* Tab Views */}
            <div className="pt-2">
              {activeTab === "bill" && (
                <BillOfStandardsView
                  standards={result.bill_of_standards || []}
                  requestId={result.request_id}
                />
              )}
              {activeTab === "audit" && (
                <CitationAuditView
                  auditResults={result.audit_results || []}
                  detectedCitations={result.cited_standards_detected || []}
                  summary={result.audit_summary || ""}
                />
              )}
              {activeTab === "gaps" && (
                <GapCheckView gapResults={result.gap_results || []} />
              )}
              {activeTab === "clauses" && (
                <ClausePackView
                  clausePack={result.clause_pack || { header: "", tender_title: "", structured_clauses: [], markdown: "" }}
                  tenderTitle={result.tender_title || result.filename || "Tender Specification"}
                  requestId={result.request_id}
                />
              )}
              {activeTab === "breakdown" && (
                <div className="space-y-4">
                  {(result.requirements || []).map((req, idx) => (
                    <div
                      key={req.id || idx}
                      className="border border-slate-800 rounded-lg bg-slate-900/70 p-4 space-y-3"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
                        <div className="font-mono text-xs font-bold text-slate-300">
                          Clause #{req.index ?? idx + 1} ({req.category || "Specification"})
                        </div>
                        <StatusBadge status={req.status} />
                      </div>
                      <p className="text-xs text-slate-200 bg-slate-950 p-2.5 rounded border border-slate-800/80 font-mono">
                        {req.clause_text}
                      </p>

                      {/* Prominent Warning if CLOSE_BUT_NOT_EXACT */}
                      {req.status === "CLOSE_BUT_NOT_EXACT" && (
                        <div className="p-3 bg-orange-950/40 border border-orange-800 rounded text-xs text-orange-200 space-y-1">
                          <div className="font-bold flex items-center gap-1.5 text-orange-300">
                            ⚠️ Qualifier Mismatch Notice (Not Recommended)
                          </div>
                          <div>{req.relevance_reason}</div>
                          <div className="text-[11px] text-orange-300/80 italic mt-0.5">
                            This standard is displayed for officer context only and is NEVER presented as a valid recommendation.
                          </div>
                        </div>
                      )}

                      {/* Matched Standards Detail */}
                      {req.matched_standards.length > 0 && (
                        <div className="space-y-2 pt-1">
                          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                            Retrieval Candidates:
                          </div>
                          {req.matched_standards.map((m, i) => (
                            <div
                              key={i}
                              className="p-3 rounded bg-slate-950/60 border border-slate-800 text-xs space-y-2"
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <span className="font-mono font-bold text-blue-400 text-sm">
                                  {m.standard_number}:{m.version.latest_year} — {m.full_title}
                                </span>
                                <MatchStrengthBadge
                                  strength={m.match_strength}
                                  denseRank={m.dense_rank}
                                  bm25Rank={m.bm25_rank}
                                  rerankScore={m.rerank_score}
                                />
                              </div>
                              <p className="text-slate-300 text-[11px] line-clamp-2 italic">
                                Scope: {m.scope_excerpt}
                              </p>
                              {m.needs_review && (
                                <div className="text-[11px] text-purple-300 bg-purple-950/50 p-1.5 rounded border border-purple-800">
                                  ⚠️ Data conflict notice: {m.needs_review_warning}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Government-Style Neutral Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-400 space-y-1">
          <p className="font-medium text-slate-300">
            Tender Guard — AI Recommender of Indian Standards for Procurement Specifications
          </p>
          <p className="text-[11px] text-slate-500">
            Prototype built for SIH 2026, not an official document. All recommendations must be verified by the procurement officer against the active BIS catalogue before issuance.
          </p>
        </div>
      </footer>
    </div>
  );
}
