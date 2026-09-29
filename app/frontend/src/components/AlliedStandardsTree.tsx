"use client";

import { AlliedNode } from "@/lib/types";

interface AlliedStandardsTreeProps {
  alliedStandards: Record<string, AlliedNode[]>;
}

const ROLE_DISPLAY_NAMES: Record<string, { label: string; icon: string }> = {
  normative_references: { label: "Normative References", icon: "📖" },
  test_methods: { label: "Testing & Sampling Methods", icon: "🔬" },
  terminology_and_glossary: { label: "Terminology & Symbols", icon: "🏷️" },
  safety_standards: { label: "Safety & Environmental Standards", icon: "🛡️" },
  installation_codes: { label: "Installation & Workmanship Codes", icon: "🛠️" },
  related_products: { label: "Allied Product Standards", icon: "📦" },
  superseded_standards: { label: "Superseded Historical Standards", icon: "⌛" },
};

export default function AlliedStandardsTree({ alliedStandards }: AlliedStandardsTreeProps) {
  const groups = Object.entries(alliedStandards).filter(([_, items]) => items && items.length > 0);

  if (groups.length === 0) {
    return (
      <div className="text-xs text-slate-400 italic py-2">
        No allied standards indexed in corpus for this record.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {groups.map(([groupKey, nodes]) => {
        const meta = ROLE_DISPLAY_NAMES[groupKey] || {
          label: groupKey.replace(/_/g, " ").toUpperCase(),
          icon: "📌",
        };

        return (
          <div key={groupKey} className="border border-slate-800 rounded bg-slate-900/40 p-3">
            <div className="flex items-center gap-2 mb-2">
              <span>{meta.icon}</span>
              <h5 className="text-xs font-semibold text-slate-300 tracking-wide uppercase">
                {meta.label} ({nodes.length})
              </h5>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {nodes.map((node, i) => (
                <div
                  key={`${node.standard_number}-${i}`}
                  className={`p-2.5 rounded text-xs border ${
                    node.is_stub
                      ? "bg-slate-950/50 border-dashed border-slate-700 text-slate-400"
                      : "bg-slate-850 border-slate-700 text-slate-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-mono font-bold text-blue-400">
                      {node.standard_number}
                      {node.year ? `:${node.year}` : ""}
                    </div>
                    {node.is_stub ? (
                      <span className="text-[10px] text-amber-400 bg-amber-950/60 border border-amber-800 px-1 py-0.5 rounded">
                        STUB (Out of Corpus)
                      </span>
                    ) : node.provenance?.verified ? (
                      <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-1 py-0.5 rounded">
                        Verified
                      </span>
                    ) : (
                      <span className="text-[10px] text-slate-400 bg-slate-800 px-1 py-0.5 rounded">
                        Unverified
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-300 mt-1 font-medium line-clamp-2">
                    {node.title}
                  </div>
                  {node.description && (
                    <div className="text-[11px] text-slate-400 mt-1 italic">
                      {node.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
