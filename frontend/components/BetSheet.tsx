"use client";

import { BetSelection } from "@/hooks/useBetSheet";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface BetSheetProps {
  isOpen: boolean;
  onClose: () => void;
  selections: BetSelection[];
  onRemove: (id: string) => void;
  onClear: () => void;
}

export default function BetSheet({
  isOpen,
  onClose,
  selections,
  onRemove,
  onClear,
}: BetSheetProps) {
  if (!isOpen) return null;

  return (
    <>
      <div className="bet-sheet-overlay" onClick={onClose} />
      <div className="bet-sheet-panel animate-slide-in-right">
        <div className="flex items-center justify-between p-4 border-b border-border-default bg-bg-primary">
          <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
            🧾 Bet Sheet
          </h2>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4" style={{ background: "rgba(16, 13, 24, 0.95)" }}>
          {selections.length === 0 ? (
            <div className="text-center mt-12">
              <div className="text-4xl mb-4 opacity-50">📋</div>
              <p className="text-text-secondary">Your bet sheet is empty.</p>
              <p className="text-text-muted text-sm mt-2">
                Click the + button on any player to add them here.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto table-scroll-container" style={{ maxHeight: "none", background: "transparent" }}>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-subtle">
                    <th className="px-3 py-2 text-left text-text-secondary font-medium text-xs uppercase whitespace-nowrap">Batter</th>
                    <th className="px-3 py-2 text-left text-text-secondary font-medium text-xs uppercase whitespace-nowrap">Game</th>
                    <th className="px-3 py-2 text-left text-text-secondary font-medium text-xs uppercase whitespace-nowrap">Prop</th>
                    <th className="px-3 py-2 text-center text-text-secondary font-medium text-xs uppercase whitespace-nowrap">Odds</th>
                    <th className="px-3 py-2 text-center text-text-secondary font-medium text-xs uppercase whitespace-nowrap">Probability</th>
                    <th className="px-3 py-2 text-center text-text-secondary font-medium text-xs uppercase whitespace-nowrap">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {selections.map((sel) => {
                    const parsed = parseGameString(sel.game);
                    return (
                      <tr key={sel.id} className="border-b border-border-subtle hover:bg-bg-card-hover transition-colors text-xs sm:text-sm">
                        <td className="px-3 py-3 whitespace-nowrap">
                          <span className="font-medium text-text-primary text-xs sm:text-base">{sel.batter}</span>
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap">
                          {parsed ? (
                            <div className="flex items-center gap-1">
                              <img
                                src={getTeamLogoUrl(parsed.away)}
                                alt=""
                                className="w-4 h-4 object-contain"
                                onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                              />
                              <span className="text-text-muted text-[10px] hidden sm:inline">vs</span>
                              <img
                                src={getTeamLogoUrl(parsed.home)}
                                alt=""
                                className="w-4 h-4 object-contain"
                                onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                              />
                            </div>
                          ) : (
                            <span className="text-text-secondary text-xs">{sel.game}</span>
                          )}
                        </td>
                        <td className="px-3 py-3 whitespace-nowrap">
                          <span className="text-text-secondary text-xs">{sel.prop}</span>
                        </td>
                        <td className="px-3 py-3 text-center whitespace-nowrap">
                          <span className="text-text-primary font-medium text-xs sm:text-base">{sel.odds}</span>
                        </td>
                        <td className="px-3 py-3 text-center whitespace-nowrap">
                          <span className={`font-medium text-xs ${
                            sel.probability !== "-" && parseFloat(String(sel.probability)) >= 65
                              ? "text-accent-green"
                              : "text-text-secondary"
                          }`}>
                            {sel.probability}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-center whitespace-nowrap">
                          <button
                            onClick={() => onRemove(sel.id)}
                            className="w-6 h-6 flex items-center justify-center rounded text-text-muted hover:text-accent-red hover:bg-[rgba(239,68,68,0.1)] transition-colors text-xs flex-shrink-0"
                            title="Remove"
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selections.length > 0 && (
          <div className="p-4 border-t border-border-default bg-bg-primary">
            <button
              onClick={onClear}
              className="w-full py-2.5 rounded-lg border border-border-default text-text-secondary hover:text-text-primary hover:bg-bg-card transition-colors font-medium text-xs sm:text-sm"
            >
              Clear All Selections
            </button>
          </div>
        )}
      </div>
    </>
  );
}
