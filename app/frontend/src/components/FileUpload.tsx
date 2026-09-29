"use client";

import { useCallback, useState, useRef } from "react";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  disabled?: boolean;
}

export default function FileUpload({
  onFileSelect,
  accept = ".pdf,.docx,.doc,.txt",
  disabled = false,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file) {
        setSelectedFile(file);
        onFileSelect(file);
      }
    },
    [onFileSelect, disabled]
  );

  const handleClick = () => {
    if (!disabled) inputRef.current?.click();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${
        disabled
          ? "border-slate-700 bg-slate-800/30 cursor-not-allowed opacity-50"
          : isDragging
          ? "border-amber-400 bg-amber-400/5 scale-[1.02] shadow-lg shadow-amber-500/10"
          : selectedFile
          ? "border-emerald-500/50 bg-emerald-500/5"
          : "border-slate-600 bg-slate-800/50 hover:border-amber-400/50 hover:bg-slate-800"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
        disabled={disabled}
      />

      {selectedFile ? (
        <div className="flex flex-col items-center gap-2">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/15 flex items-center justify-center text-2xl">
            📎
          </div>
          <p className="text-white font-medium">{selectedFile.name}</p>
          <p className="text-slate-400 text-sm">{formatSize(selectedFile.size)}</p>
          <p className="text-emerald-400 text-xs mt-1">Click or drop to replace</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center text-3xl">
            📤
          </div>
          <div>
            <p className="text-white font-medium">
              Drop your tender document here
            </p>
            <p className="text-slate-400 text-sm mt-1">
              or <span className="text-amber-400 underline underline-offset-2">browse files</span>
            </p>
          </div>
          <p className="text-slate-500 text-xs">
            Supports PDF, DOCX, and TXT files
          </p>
        </div>
      )}
    </div>
  );
}
