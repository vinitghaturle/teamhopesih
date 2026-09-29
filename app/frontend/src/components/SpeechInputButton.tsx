"use client";

import { useState, useEffect } from "react";

interface SpeechInputButtonProps {
  onTranscript: (text: string) => void;
  language?: string; // "en" | "hi" | "mr" | "auto"
  disabled?: boolean;
}

export default function SpeechInputButton({
  onTranscript,
  language = "en",
  disabled = false,
}: SpeechInputButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setIsSupported(false);
        return;
      }

      const rec = new SpeechRecognition();
      rec.continuous = false;
      rec.interimResults = false;

      rec.onstart = () => setIsListening(true);
      rec.onend = () => setIsListening(false);
      rec.onerror = (e: any) => {
        console.warn("Speech recognition error:", e.error);
        setIsListening(false);
      };

      rec.onresult = (event: any) => {
        if (event.results && event.results[0] && event.results[0][0]) {
          const transcript = event.results[0][0].transcript;
          onTranscript(transcript);
        }
      };

      setRecognition(rec);
    }
  }, [onTranscript]);

  const toggleListening = () => {
    if (!recognition) return;

    if (isListening) {
      recognition.stop();
    } else {
      // Map language code to BCP-47 for Indian variants
      let langCode = "en-IN";
      if (language === "hi") langCode = "hi-IN";
      else if (language === "mr") langCode = "mr-IN";
      else if (language === "auto") langCode = "en-IN";

      recognition.lang = langCode;
      try {
        recognition.start();
      } catch (err) {
        console.error("Speech recognition start failed:", err);
      }
    }
  };

  if (!isSupported) {
    return (
      <span
        title="Web Speech API is not supported in this browser (Use Chrome or Edge for voice dictation)"
        className="text-[11px] text-slate-500 italic flex items-center gap-1 cursor-help"
      >
        <span>🎙️</span>
        <span className="hidden sm:inline">Voice not supported in browser</span>
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={toggleListening}
      disabled={disabled}
      title={
        isListening
          ? "Listening... Speak your tender specifications now"
          : `Click to dictate specifications (${language === "hi" ? "Hindi hi-IN" : language === "mr" ? "Marathi mr-IN" : "English en-IN"})`
      }
      className={`px-3 py-1.5 rounded text-xs font-semibold flex items-center gap-1.5 transition-all ${
        isListening
          ? "bg-red-600 text-white animate-pulse shadow-lg ring-2 ring-red-400"
          : "bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700"
      }`}
    >
      <span>{isListening ? "🔴" : "🎙️"}</span>
      <span>{isListening ? "Listening..." : "Dictate Spec"}</span>
    </button>
  );
}
