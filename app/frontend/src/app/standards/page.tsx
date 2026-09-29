"use client";

import { useEffect, useState } from "react";
import { listStandards, listSectors } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import StandardCard, { StandardItem } from "@/components/StandardCard";

export default function StandardsLibraryPage() {
  const [standards, setStandards] = useState<StandardItem[]>([]);
  const [sectors, setSectors] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedSector, setSelectedSector] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [stds, secs] = await Promise.all([
          listStandards(),
          listSectors(),
        ]);
        setStandards(stds);
        setSectors(secs);
      } catch {
        console.error("Failed to load standards");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const results = await listStandards(search, selectedSector || undefined);
      setStandards(results);
    } catch {
      console.error("Search failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch();
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, selectedSector]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">
          📚 Standards Library
        </h1>
        <p className="text-slate-400">
          Browse and search the Indian Standards (IS) knowledge base. {standards.length} standards available.
        </p>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by IS number, title, or keywords..."
            className="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-slate-200 text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/50 transition-all"
          />
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500">
            🔍
          </span>
        </div>
        <select
          value={selectedSector}
          onChange={(e) => setSelectedSector(e.target.value)}
          className="bg-slate-800/50 border border-slate-700 rounded-xl px-4 py-2.5 text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/50 min-w-[180px]"
        >
          <option value="">All Sectors</option>
          {sectors.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {/* Results */}
      {loading ? (
        <LoadingSpinner message="Loading standards..." />
      ) : standards.length === 0 ? (
        <div className="text-center py-12 bg-slate-800/30 border border-slate-700/30 rounded-2xl">
          <div className="text-4xl mb-3 opacity-40">🔍</div>
          <p className="text-slate-400">No standards found matching your search.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {standards.map((std) => (
            <StandardCard key={std.id} standard={std} />
          ))}
        </div>
      )}
    </div>
  );
}
