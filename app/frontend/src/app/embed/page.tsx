"use client";

import { useState } from "react";
import { analyzeTender } from "@/lib/api";
import StatusBadge from "@/components/StatusBadge";

export default function EmbedWidgetPage() {
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);

  const handleAnalyze = async () => {
    if (!inputText.trim()) return;
    setIsLoading(true);
    try {
      const data = await analyzeTender({ text: inputText.trim() });
      setResult(data);
    } catch (err) {
      console.error("Widget analyze failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const embedCode = `<iframe 
  src="http://localhost:3000/embed" 
  width="100%" 
  height="600" 
  style="border: 1px solid #334155; border-radius: 8px;"
  title="Tender Guard BIS Standards Recommender">
</iframe>`;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 font-sans text-xs space-y-4">
      {/* Widget Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-blue-700 text-white rounded font-bold text-xs flex items-center justify-center">
            TG
          </div>
          <div>
            <div className="font-bold text-slate-200">Tender Guard Embeddable Widget</div>
            <div className="text-[10px] text-slate-400">BIS Indian Standards Verification Plug-in</div>
          </div>
        </div>
        <button
          type="button"
          onClick={() => {
            navigator.clipboard.writeText(embedCode);
            setCopiedSnippet(true);
            setTimeout(() => setCopiedSnippet(false), 2000);
          }}
          className="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 text-blue-400 border border-slate-700 rounded text-[11px] font-semibold flex items-center gap-1"
        >
          <span>📋</span>
          <span>{copiedSnippet ? "Copied!" : "Copy Embed HTML"}</span>
        </button>
      </div>

      {/* Input Box */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-2">
        <textarea
          rows={4}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Enter or paste requirement text here (e.g. 'Ordinary Portland cement 43 grade conforming to IS 8112:1989')..."
          className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-blue-500"
        />
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleAnalyze}
            disabled={isLoading || !inputText.trim()}
            className="px-4 py-1.5 bg-blue-700 hover:bg-blue-600 text-white text-xs font-bold rounded shadow disabled:opacity-50"
          >
            {isLoading ? "Analyzing..." : "🔍 Check Standards"}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {result && (
        <div className="space-y-3">
          {/* Stale Citations */}
          {result.audit_results && result.audit_results.length > 0 && (
            <div className="p-3 bg-rose-950/40 border border-rose-800 rounded space-y-1.5">
              <div className="font-bold text-rose-300 flex items-center gap-1">
                <span>⚠️</span> Stale Reference Audit:
              </div>
              {result.audit_results.map((a: any, i: number) => (
                <div key={i} className="text-[11px] text-slate-200 font-mono">
                  • <b>{a.citation}</b>: {a.status} (Latest: {a.standard_number}:{a.latest_year})
                </div>
              ))}
            </div>
          )}

          {/* Recommended Standards */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3 space-y-2">
            <div className="font-bold text-slate-300 text-xs">Applicable Standards:</div>
            {result.bill_of_standards && result.bill_of_standards.length > 0 ? (
              result.bill_of_standards.map((s: any, i: number) => (
                <div key={i} className="p-2 bg-slate-950 border border-slate-800 rounded space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-blue-400">
                      {s.standard_number}:{s.version?.latest_year}
                    </span>
                    {s.is_compulsory_certification && (
                      <span className="text-[9px] bg-red-950 text-red-300 border border-red-800 px-1 py-0.2 rounded font-bold">
                        QCO MANDATORY
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-300">{s.full_title}</p>
                </div>
              ))
            ) : (
              <div className="text-slate-400 italic">No confident standard match found.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
