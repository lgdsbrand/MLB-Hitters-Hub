"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { BetSelection, useBetSheet } from "@/hooks/useBetSheet";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

export default function BetSheetPage() {
  const betSheet = useBetSheet();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <header className="flex items-center justify-between gap-6 mb-10">
        <div className="flex flex-col items-start">
          <div className="text-accent-teal text-xs tracking-[0.2em] uppercase font-bold mb-1">
            Bet Management
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">
            🧾 Bet Sheet
          </h1>
          <p className="text-text-secondary text-sm mt-2">
            Total Bets: <span className="font-bold text-accent-green">{betSheet.count}</span>
          </p>
        </div>

        <Link
          href="/"
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-bg-card border border-border-default hover:border-accent-teal transition-colors text-text-primary text-sm font-medium"
        >
          ← Back to Hub
        </Link>
      </header>

      {/* Main Content */}
      <div className="bg-bg-card rounded-xl border border-border-default overflow-hidden">
        {betSheet.count === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4">
            <div className="text-6xl mb-4 opacity-50">📋</div>
            <h2 className="text-2xl font-bold text-text-primary mb-2">Bet Sheet Empty</h2>
            <p className="text-text-secondary mb-6 text-center max-w-md">
              Your bet sheet is currently empty. Head back to the hub and click the + button on any player to start building your bets.
            </p>
            <Link
              href="/"
              className="px-6 py-2.5 rounded-lg bg-accent-green text-bg-primary font-bold hover:opacity-90 transition-opacity"
            >
              Go to Hub
            </Link>
          </div>
        ) : (
          <>
            {/* Action Buttons */}
            <div className="flex items-center justify-between p-4 border-b border-border-default bg-bg-primary">
              <div className="flex items-center gap-3">
                <span className="text-sm text-text-secondary">
                  {betSheet.count} bet{betSheet.count !== 1 ? "s" : ""} selected
                </span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={betSheet.clearAll}
                  className="px-4 py-1.5 rounded text-sm border border-red-500/50 text-red-400 hover:bg-red-500/10 transition-colors"
                >
                  Clear All
                </button>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto table-scroll-container" style={{ maxHeight: "none" }}>
              <table className="w-full text-sm" style={{ minWidth: "700px" }}>
                <thead>
                  <tr className="border-b border-border-default bg-bg-primary/50">
                    <th className="px-4 py-3 text-left text-text-secondary font-medium text-xs uppercase">Batter</th>
                    <th className="px-4 py-3 text-left text-text-secondary font-medium text-xs uppercase">Game</th>
                    <th className="px-4 py-3 text-left text-text-secondary font-medium text-xs uppercase">Source</th>
                    <th className="px-4 py-3 text-left text-text-secondary font-medium text-xs uppercase">Prop</th>
                    <th className="px-4 py-3 text-center text-text-secondary font-medium text-xs uppercase">Odds</th>
                    <th className="px-4 py-3 text-center text-text-secondary font-medium text-xs uppercase">Probability</th>
                    <th className="px-4 py-3 text-center text-text-secondary font-medium text-xs uppercase">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {betSheet.selections.map((sel) => {
                    const parsed = parseGameString(sel.game);
                    return (
                      <tr key={sel.id} className="border-b border-border-subtle hover:bg-bg-card-hover transition-colors">
                        <td className="px-4 py-3">
                          <span className="font-medium text-text-primary">{sel.batter}</span>
                        </td>
                        <td className="px-4 py-3">
                          {parsed ? (
                            <div className="flex items-center gap-2">
                              <img
                                src={getTeamLogoUrl(parsed.away)}
                                alt=""
                                className="w-5 h-5 object-contain"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = "none";
                                }}
                              />
                              <span className="text-text-muted text-[10px]">@</span>
                              <img
                                src={getTeamLogoUrl(parsed.home)}
                                alt=""
                                className="w-5 h-5 object-contain"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display = "none";
                                }}
                              />
                              <span className="text-xs text-text-secondary ml-1">
                                {parsed.away} @ {parsed.home}
                              </span>
                            </div>
                          ) : (
                            <span className="text-text-secondary text-xs">{sel.game}</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-bg-primary text-text-secondary">
                            {sel.source}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-text-secondary text-xs font-medium">{sel.prop}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="text-text-primary font-medium">{sel.odds}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span
                            className={`font-medium ${
                              sel.probability !== "-" &&
                              parseFloat(String(sel.probability)) >= 65
                                ? "text-accent-green"
                                : "text-text-secondary"
                            }`}
                          >
                            {sel.probability}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <button
                            onClick={() => betSheet.removePlayer(sel.id)}
                            className="text-red-400 hover:text-red-300 transition-colors text-sm font-medium"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Summary Section */}
            <div className="p-4 border-t border-border-default bg-bg-primary/50">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-bg-card border border-border-subtle">
                  <div className="text-text-secondary text-xs uppercase tracking-wider font-bold mb-1">
                    Total Bets
                  </div>
                  <div className="text-3xl font-bold text-accent-green">{betSheet.count}</div>
                </div>
                <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-bg-card border border-border-subtle">
                  <div className="text-text-secondary text-xs uppercase tracking-wider font-bold mb-1">
                    High Confidence
                  </div>
                  <div className="text-3xl font-bold text-accent-green">
                    {betSheet.selections.filter(
                      (s) => s.probability !== "-" && parseFloat(String(s.probability)) >= 65
                    ).length}
                  </div>
                </div>
                <div className="flex flex-col items-center justify-center p-4 rounded-lg bg-bg-card border border-border-subtle">
                  <div className="text-text-secondary text-xs uppercase tracking-wider font-bold mb-1">
                    Added Today
                  </div>
                  <div className="text-3xl font-bold text-text-primary">{betSheet.count}</div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
