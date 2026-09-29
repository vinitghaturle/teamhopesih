"use client";

interface MatchStrengthBadgeProps {
  strength: string;
  denseRank?: number | null;
  bm25Rank?: number | null;
  rerankScore?: number | null;
  className?: string;
}

export default function MatchStrengthBadge({
  strength,
  denseRank,
  bm25Rank,
  rerankScore,
  className = "",
}: MatchStrengthBadgeProps) {
  const norm = (strength || "").toUpperCase();

  let style = "bg-slate-800 text-slate-300 border-slate-700";
  let label = "LOW MATCH";

  if (norm === "HIGH" || norm === "EXACT") {
    style = "bg-emerald-950/80 text-emerald-300 border-emerald-800";
    label = "HIGH STRENGTH";
  } else if (norm === "MEDIUM" || norm === "LIKELY") {
    style = "bg-blue-950/80 text-blue-300 border-blue-800";
    label = "MEDIUM STRENGTH";
  } else if (norm === "CLOSE_BUT_NOT_EXACT") {
    style = "bg-orange-950/80 text-orange-300 border-orange-800";
    label = "CLOSE (QUALIFIER MISMATCH)";
  } else if (norm === "NO_CONFIDENT_MATCH") {
    style = "bg-slate-900 text-slate-400 border-slate-700";
    label = "REFUSED (BELOW FLOOR)";
  }

  return (
    <div className={`inline-flex flex-col items-start gap-1 ${className}`}>
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold border ${style}`}>
        {label}
      </span>
      {(denseRank !== undefined || bm25Rank !== undefined || rerankScore !== undefined) && (
        <span className="text-[10px] text-slate-400 font-mono">
          {[
            denseRank !== null && denseRank !== undefined ? `Dense: #${denseRank}` : null,
            bm25Rank !== null && bm25Rank !== undefined ? `BM25: #${bm25Rank}` : null,
            rerankScore !== null && rerankScore !== undefined ? `CE: ${rerankScore.toFixed(2)}` : null,
          ]
            .filter(Boolean)
            .join(" | ")}
        </span>
      )}
    </div>
  );
}
