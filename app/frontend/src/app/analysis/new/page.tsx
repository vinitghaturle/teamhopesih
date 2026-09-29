"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import FileUpload from "@/components/FileUpload";
import LoadingSpinner from "@/components/LoadingSpinner";
import { extractRequirements, getSampleTenders } from "@/lib/api";

export default function NewAnalysisPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"upload" | "paste">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingSamples, setLoadingSamples] = useState(false);

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);

    try {
      const result = await extractRequirements(
        mode === "upload" ? file || undefined : undefined,
        mode === "paste" ? text : undefined
      );
      // Navigate to home page
      router.push(`/`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setLoading(false);
    }
  };

  const loadSampleTender = async () => {
    setLoadingSamples(true);
    try {
      const samples = await getSampleTenders();
      if (samples.length > 0) {
        // Pick a random sample
        const sample = samples[Math.floor(Math.random() * samples.length)];
        setText(sample.text);
        setMode("paste");
      }
    } catch {
      setError("Failed to load sample tenders");
    } finally {
      setLoadingSamples(false);
    }
  };

  const canSubmit = mode === "upload" ? !!file : text.trim().length > 50;

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-12">
          <LoadingSpinner message="Analyzing tender document..." />
          <p className="text-center text-slate-500 text-sm mt-4">
            Extracting technical, performance, and safety requirements using AI.
            <br />
            This may take a few seconds.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">New Analysis</h1>
        <p className="text-slate-400">
          Upload a procurement tender document or paste the text to extract requirements and find applicable Indian Standards.
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="flex gap-2 mb-6 bg-slate-800/50 p-1 rounded-xl w-fit">
        <button
          onClick={() => setMode("upload")}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
            mode === "upload"
              ? "bg-amber-500/20 text-amber-400 shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          📤 Upload File
        </button>
        <button
          onClick={() => setMode("paste")}
          className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
            mode === "paste"
              ? "bg-amber-500/20 text-amber-400 shadow-sm"
              : "text-slate-400 hover:text-white"
          }`}
        >
          📝 Paste Text
        </button>
      </div>

      {/* Input Area */}
      <div className="bg-slate-800/30 border border-slate-700/50 rounded-2xl p-6 mb-6">
        {mode === "upload" ? (
          <FileUpload onFileSelect={setFile} />
        ) : (
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-slate-300">
                Tender Text
              </label>
              <button
                onClick={loadSampleTender}
                disabled={loadingSamples}
                className="text-xs text-amber-400 hover:text-amber-300 transition-colors disabled:opacity-50"
              >
                {loadingSamples ? "Loading..." : "📋 Load Sample Tender"}
              </button>
            </div>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste your tender document text here..."
              rows={16}
              className="w-full bg-slate-900/50 border border-slate-700 rounded-xl p-4 text-slate-200 text-sm leading-relaxed placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500/50 resize-y transition-all"
            />
            <p className="text-slate-500 text-xs mt-2">
              {text.length} characters · Minimum 50 characters required
            </p>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          ❌ {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        className="w-full py-3.5 rounded-xl font-semibold text-sm transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-400 hover:to-orange-400 hover:shadow-lg hover:shadow-amber-500/25 active:scale-[0.98]"
      >
        🔍 Analyze & Extract Requirements
      </button>

      {/* Info */}
      <div className="mt-8 p-4 rounded-xl bg-slate-800/30 border border-slate-700/30">
        <h3 className="text-sm font-medium text-slate-300 mb-3">How it works</h3>
        <div className="grid sm:grid-cols-3 gap-4">
          {[
            { step: "1", label: "Upload", desc: "Submit your tender document" },
            { step: "2", label: "Extract", desc: "AI identifies all requirements" },
            { step: "3", label: "Match", desc: "Get recommended IS standards" },
          ].map((item) => (
            <div key={item.step} className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-full bg-amber-500/15 text-amber-400 text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                {item.step}
              </div>
              <div>
                <p className="text-white text-sm font-medium">{item.label}</p>
                <p className="text-slate-500 text-xs">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
