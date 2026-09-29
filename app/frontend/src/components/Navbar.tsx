"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Analyze Tender", icon: "📋" },
    { href: "/standards", label: "Standards Catalogue", icon: "📚" },
    { href: "/portal-demo", label: "Portal Demo (Simulated)", icon: "🌐" },
    { href: "/embed", label: "Embed Widget", icon: "🧩" },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-700 text-white rounded font-bold text-sm flex items-center justify-center tracking-wider">
              TG
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-semibold text-slate-100 tracking-tight">
                  TENDER GUARD
                </span>
                <span className="bg-blue-900/60 text-blue-300 text-[10px] font-medium px-1.5 py-0.5 rounded border border-blue-700/50">
                  SIH 2026
                </span>
              </div>
              <p className="text-[11px] text-slate-400 -mt-0.5">
                Indian Standards (BIS) Recommender & Specification Auditor
              </p>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-2">
            {links.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3.5 py-1.5 rounded text-xs font-medium transition-colors ${
                    isActive
                      ? "bg-slate-800 text-blue-400 border border-slate-700"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                  }`}
                >
                  <span className="mr-1.5">{link.icon}</span>
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
