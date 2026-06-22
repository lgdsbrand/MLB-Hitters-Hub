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

        <div className="flex-1 overflow-y-auto p-4">
          {selections.length === 0 ? (
            <div className="text-center mt-12">
              <div className="text-4xl mb-4 opacity-50">📋</div>
              <p className="text-text-secondary">Your bet sheet is empty.</p>
              <p className="text-text-muted text-sm mt-2">
                Click the + button on any player to add them here.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {selections.map((sel) => {
                const parsed = parseGameString(sel.game);
                return (
                  <div
                    key={sel.id}
                    className="flex items-center justify-between bg-bg-card p-3 rounded-lg border border-border-subtle hover:border-border-default transition-colors"
                  >
                    <div>
                      <div className="font-bold text-sm text-text-primary">
                        {sel.batter}
                      </div>
                      <div className="flex items-center gap-1 mt-1">
                        {parsed && (
                          <>
                            <img
                              src={getTeamLogoUrl(parsed.away)}
                              alt=""
                              className="w-3 h-3 object-contain"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = "none";
                              }}
                            />
                            <span className="text-text-muted text-[10px]">@</span>
                            <img
                              src={getTeamLogoUrl(parsed.home)}
                              alt=""
                              className="w-3 h-3 object-contain"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = "none";
                              }}
                            />
                          </>
                        )}
                        <span className="text-text-muted text-[10px] uppercase tracking-wider ml-1">
                          {sel.source}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => onRemove(sel.id)}
                      className="w-7 h-7 flex items-center justify-center rounded bg-bg-primary text-text-muted hover:text-accent-red hover:bg-[rgba(239,68,68,0.1)] transition-colors"
                      title="Remove"
                    >
                      ✕
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {selections.length > 0 && (
          <div className="p-4 border-t border-border-default bg-bg-primary">
            <button
              onClick={onClear}
              className="w-full py-2.5 rounded-lg border border-border-default text-text-secondary hover:text-text-primary hover:bg-bg-card transition-colors font-medium text-sm"
            >
              Clear All Selections
            </button>
          </div>
        )}
      </div>
    </>
  );
}
