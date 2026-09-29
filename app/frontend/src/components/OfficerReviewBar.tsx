"use client";

import { useState, useEffect } from "react";

interface OfficerReviewBarProps {
  requestId: string;
  standardNumber: string;
  initialAction?: "ACCEPT" | "REJECT" | "FLAG" | null;
  initialRemarks?: string;
  onReviewUpdated?: (action: "ACCEPT" | "REJECT" | "FLAG", remarks: string) => void;
}

export default function OfficerReviewBar({
  requestId,
  standardNumber,
  initialAction = null,
  initialRemarks = "",
  onReviewUpdated,
}: OfficerReviewBarProps) {
  const [currentAction, setCurrentAction] = useState<"ACCEPT" | "REJECT" | "FLAG" | null>(initialAction);
  const [remarks, setRemarks] = useState(initialRemarks);
  const [showRemarksInput, setShowRemarksInput] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    // Fetch any saved review for this standard & request_id
    if (!requestId) return;
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    fetch(`${backendUrl}/api/reviews/${requestId}`)
      .then((res) => (res.ok ? res.json() : []))
      .then((reviews: any[]) => {
        const found = reviews.find(
          (r) => r.standard_number.toUpperCase() === standardNumber.toUpperCase()
        );
        if (found) {
          setCurrentAction(found.action);
          setRemarks(found.remarks || "");
        }
      })
      .catch(() => {});
  }, [requestId, standardNumber]);

  const handleAction = async (action: "ACCEPT" | "REJECT" | "FLAG") => {
    setIsSaving(true);
    setSaveSuccess(false);
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

    try {
      const res = await fetch(`${backendUrl}/api/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id: requestId,
          standard_number: standardNumber,
          action: action,
          remarks: remarks.trim() || undefined,
          officer_name: "Procurement Officer",
        }),
      });

      if (res.ok) {
        setCurrentAction(action);
        setSaveSuccess(true);
        if (onReviewUpdated) {
          onReviewUpdated(action, remarks);
        }
        setTimeout(() => setSaveSuccess(false), 2500);
      }
    } catch (err) {
      console.error("Failed to persist officer review:", err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-slate-950/80 border border-slate-800 rounded p-3 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
            Officer Review:
          </span>
          {currentAction && (
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                currentAction === "ACCEPT"
                  ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                  : currentAction === "REJECT"
                  ? "bg-rose-950 text-rose-300 border-rose-800"
                  : "bg-amber-950 text-amber-300 border-amber-800"
              }`}
            >
              {currentAction === "ACCEPT" && "✓ APPROVED FOR TENDER"}
              {currentAction === "REJECT" && "✕ EXCLUDED FROM TENDER"}
              {currentAction === "FLAG" && "⚠️ FLAGGED FOR SUPERVISOR"}
            </span>
          )}
          {saveSuccess && (
            <span className="text-[10px] text-emerald-400 font-semibold animate-pulse">
              Saved to audit database
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            disabled={isSaving}
            onClick={() => handleAction("ACCEPT")}
            className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
              currentAction === "ACCEPT"
                ? "bg-emerald-600 text-white shadow"
                : "bg-slate-800 text-slate-300 hover:bg-emerald-950 hover:text-emerald-300 hover:border-emerald-700 border border-slate-700"
            }`}
          >
            ✓ Accept
          </button>
          <button
            type="button"
            disabled={isSaving}
            onClick={() => handleAction("REJECT")}
            className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
              currentAction === "REJECT"
                ? "bg-rose-600 text-white shadow"
                : "bg-slate-800 text-slate-300 hover:bg-rose-950 hover:text-rose-300 hover:border-rose-700 border border-slate-700"
            }`}
          >
            ✕ Reject
          </button>
          <button
            type="button"
            disabled={isSaving}
            onClick={() => {
              setShowRemarksInput(true);
              handleAction("FLAG");
            }}
            className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
              currentAction === "FLAG"
                ? "bg-amber-600 text-white shadow"
                : "bg-slate-800 text-slate-300 hover:bg-amber-950 hover:text-amber-300 hover:border-amber-700 border border-slate-700"
            }`}
          >
            🚩 Flag
          </button>
          <button
            type="button"
            onClick={() => setShowRemarksInput(!showRemarksInput)}
            className="text-[11px] text-slate-400 hover:text-slate-200 underline ml-1"
          >
            {showRemarksInput ? "Hide Note" : "Add Note"}
          </button>
        </div>
      </div>

      {showRemarksInput && (
        <div className="pt-2 flex gap-2">
          <input
            type="text"
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            placeholder="Enter reason, supervisor note, or amendment override remarks..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded px-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="button"
            onClick={() => handleAction(currentAction || "FLAG")}
            disabled={isSaving}
            className="px-3 py-1 bg-blue-700 hover:bg-blue-600 text-white text-xs font-semibold rounded"
          >
            Save Note
          </button>
        </div>
      )}
    </div>
  );
}
