"use client";

import React, { useState } from "react";

export interface StandardItem {
  id: number;
  is_number: string;
  title: string;
  year?: number | null;
  scope?: string | null;
  keywords?: string | null;
  sector?: string | null;
}

interface StandardCardProps {
  standard: StandardItem;
}

export default function StandardCard({ standard }: StandardCardProps) {
  const [expanded, setExpanded] = useState(false);

  const parseKeywords = (kw?: string | null): string[] => {
    if (!kw) return [];
    try {
      return JSON.parse(kw);
    } catch {
      return [];
    }
  };

  return (
    <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl overflow-hidden hover:border-slate-600/50 transition-all">
      <div
        className="flex items-center gap-4 px-5 py-4 cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-shrink-0">
          <span className="text-amber-400 font-mono text-sm font-medium bg-amber-500/10 px-2.5 py-1 rounded-lg">
            {standard.is_number}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-white text-sm font-medium truncate">
            {standard.title}
          </h3>
        </div>
        {standard.sector && (
          <span className="hidden sm:inline-flex px-2.5 py-0.5 bg-slate-700/50 text-slate-300 text-xs rounded-full flex-shrink-0">
            {standard.sector}
          </span>
        )}
        {standard.year && (
          <span className="text-slate-500 text-xs flex-shrink-0">
            {standard.year}
          </span>
        )}
        <span
          className="text-slate-500 text-xs flex-shrink-0 transition-transform duration-200"
          style={{ transform: expanded ? "rotate(180deg)" : "" }}
        >
          ▼
        </span>
      </div>

      {expanded && (
        <div className="px-5 pb-4 pt-0 border-t border-slate-700/30">
          <div className="pl-[calc(2.5rem+1rem)] space-y-3 pt-3">
            {standard.scope && (
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">
                  Scope
                </p>
                <p className="text-slate-300 text-sm leading-relaxed">
                  {standard.scope}
                </p>
              </div>
            )}
            {standard.keywords && (
              <div>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">
                  Keywords
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {parseKeywords(standard.keywords).map((kw, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-0.5 bg-slate-700/50 text-slate-300 text-xs rounded-md"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
            <div className="flex items-center gap-4 text-xs text-slate-500 pt-1">
              {standard.sector && <span>Sector: {standard.sector}</span>}
              {standard.year && <span>Year: {standard.year}</span>}
              <span>ID: {standard.id}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
