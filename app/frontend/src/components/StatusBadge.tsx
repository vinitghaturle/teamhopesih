"use client";

interface StatusBadgeProps {
  status: string;
  className?: string;
  isUnverified?: boolean;
}

export default function StatusBadge({ status, className = "", isUnverified = false }: StatusBadgeProps) {
  const normStatus = (status || "").toUpperCase();

  let badgeStyle = "bg-slate-800 text-slate-300 border-slate-700";
  let label = normStatus;

  switch (normStatus) {
    case "CURRENT":
      badgeStyle = "bg-emerald-950/80 text-emerald-300 border-emerald-800";
      label = "CURRENT";
      break;
    case "AMENDED":
      badgeStyle = "bg-blue-950/80 text-blue-300 border-blue-800";
      label = "AMENDED";
      break;
    case "SUPERSEDED":
      badgeStyle = "bg-rose-950/80 text-rose-300 border-rose-800";
      label = "SUPERSEDED";
      break;
    case "YEAR_OUTDATED":
      badgeStyle = "bg-amber-950/80 text-amber-300 border-amber-800";
      label = "YEAR OUTDATED";
      break;
    case "NEEDS_REVIEW":
      badgeStyle = "bg-purple-950/80 text-purple-300 border-purple-800";
      label = "NEEDS REVIEW";
      break;
    case "CLOSE_BUT_NOT_EXACT":
      badgeStyle = "bg-orange-950/80 text-orange-300 border-orange-800";
      label = "CLOSE BUT NOT EXACT";
      break;
    case "NO_CONFIDENT_MATCH":
      badgeStyle = "bg-slate-900 text-slate-400 border-slate-700";
      label = "NO CONFIDENT MATCH";
      break;
    case "NOT_IN_CORPUS":
      badgeStyle = "bg-slate-900 text-slate-400 border-slate-700";
      label = "NOT IN CORPUS";
      break;
    default:
      badgeStyle = "bg-slate-800 text-slate-300 border-slate-700";
  }

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold tracking-wide border uppercase ${badgeStyle} ${className}`}>
        {label}
      </span>
      {isUnverified && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-950/60 text-amber-400 border border-amber-800/60 uppercase">
          Unverified
        </span>
      )}
    </span>
  );
}
