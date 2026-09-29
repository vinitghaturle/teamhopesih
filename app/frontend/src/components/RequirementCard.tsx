"use client";

import React from "react";
import RecommendationTable, { RecommendationItem } from "./RecommendationTable";

const REQ_TYPE_COLORS: Record<string, string> = {
  technical: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  safety: "bg-red-500/15 text-red-400 border-red-500/30",
  quality: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  material: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  performance: "bg-amber-500/15 text-amber-400 border-amber-500/30",
};

export interface RequirementData {
  requirement_id: number;
  req_type: string;
  description: string;
  keywords?: string | null;
  recommendations: RecommendationItem[];
}

interface RequirementCardProps {
  index: number;
  requirement: RequirementData;
  hasRecommendations: boolean;
  onDecision: (recId: number, decision: "accept" | "reject" | "flag") => void;
}

export default function RequirementCard({
  index,
  requirement,
  hasRecommendations,
  onDecision,
}: RequirementCardProps) {
  const parseKeywords = (kw?: string | null): string[] => {
    if (!kw) return [];
    try {
      return JSON.parse(kw);
    } catch {
      return [];
    }
  };

  const keywords = parseKeywords(requirement.keywords);

  return (
    <div className="bg-slate-800/30 border border-slate-700/30 rounded-2xl overflow-hidden">
      {/* Requirement Header */}
      <div className="p-5 border-b border-slate-700/30">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-slate-700/50 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            {index + 1}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                  REQ_TYPE_COLORS[requirement.req_type.toLowerCase()] ||
                  "bg-slate-700/50 text-slate-300 border-slate-600"
                }`}
              >
                {requirement.req_type.toUpperCase()}
              </span>
            </div>
            <p className="text-slate-200 text-sm leading-relaxed">
              {requirement.description}
            </p>
            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {keywords.map((kw, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 bg-slate-700/50 text-slate-400 text-xs rounded-md"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {requirement.recommendations.length > 0 ? (
        <RecommendationTable
          recommendations={requirement.recommendations}
          onDecision={onDecision}
        />
      ) : !hasRecommendations ? (
        <div className="p-6 text-center text-slate-500 text-sm">
          Click &quot;Get Recommendations&quot; to find matching Indian Standards.
        </div>
      ) : (
        <div className="p-6 text-center text-slate-500 text-sm">
          No matching Indian Standards found for this requirement.
        </div>
      )}
    </div>
  );
}
