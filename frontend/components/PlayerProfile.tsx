"use client";

import { useMemo } from "react";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface PlayerStats {
  [key: string]: unknown;
}

interface PlayerProfileProps {
  isOpen: boolean;
  onClose: () => void;
  playerName: string;
  game: string;
  hitsData: PlayerStats | null;
  hrData: PlayerStats | null;
  tbData: PlayerStats | null;
  bvpData: PlayerStats | null;
}

function StatRow({ label, value, icon, color }: { label: string; value: any; icon?: string; color?: string }) {
  const displayValue = value === "-" || value === "" || value === null ? "-" : value;
  const textColor = color || "var(--color-text-primary)";
  
  // Check if value is a percentage
  const isPercentage = typeof displayValue === 'string' && displayValue.includes('%');
  const percentageValue = isPercentage ? parseFloat(displayValue.replace('%', '')) : 0;
  
  // Determine bar color based on percentage - subtle accent colors
  const getBarColor = (pct: number) => {
    if (pct >= 70) return 'linear-gradient(90deg, #22c55e, #4ade80)';
    if (pct >= 50) return 'linear-gradient(90deg, #f59e0b, #fbbf24)';
    if (pct >= 30) return 'linear-gradient(90deg, #f97316, #fb923c)';
    return 'linear-gradient(90deg, #ef4444, #f87171)';
  };

  // Check if value is numeric (for stat badges)
  const isNumeric = !isNaN(parseFloat(String(displayValue))) && displayValue !== "-";

  return (
    <div 
      className="flex items-center justify-between py-3 px-4 rounded-xl border transition-all duration-300 hover:scale-[1.01]"
      style={{ 
        background: "rgba(255, 255, 255, 0.03)",
        borderColor: "var(--color-border-subtle)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.3)";
        e.currentTarget.style.background = "rgba(139, 92, 246, 0.05)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--color-border-subtle)";
        e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
      }}
    >
      <div className="flex items-center gap-3 flex-1">
        {icon && <span className="text-lg" style={{ minWidth: '24px' }}>{icon}</span>}
        <span className="text-text-secondary text-sm font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-3">
        {isPercentage && percentageValue > 0 && (
          <div className="w-24 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255, 255, 255, 0.1)' }}>
            <div 
              className="h-full rounded-full transition-all duration-500"
              style={{ 
                width: `${Math.min(percentageValue, 100)}%`,
                background: getBarColor(percentageValue)
              }}
            />
          </div>
        )}
        <span 
          className="font-semibold text-base"
          style={{ 
            color: textColor, 
            minWidth: '40px', 
            textAlign: 'right'
          }}
        >
          {displayValue}
        </span>
      </div>
    </div>
  );
}

function StatGrid({ title, stats, icon }: { title: string; stats: Record<string, any>; icon: string }) {
  const sortedEntries = useMemo(() => {
    const ignore = ["Batter", "Pitcher", "Game", "Name", "Team", "Icon"];
    return Object.entries(stats)
      .filter(([key]) => !ignore.includes(key) && stats[key] !== null && stats[key] !== undefined)
      .slice(0, 12);
  }, [stats]);

  if (sortedEntries.length === 0) return null;

  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 mb-4 px-1">
        <span className="text-2xl">{icon}</span>
        <h3 className="font-semibold text-text-primary text-base">{title}</h3>
      </div>
      <div className="grid grid-cols-1 gap-2.5">
        {sortedEntries.map(([key, value]) => (
          <StatRow key={key} label={key} value={value} />
        ))}
      </div>
    </div>
  );
}

export default function PlayerProfile({
  isOpen,
  onClose,
  playerName,
  game,
  hitsData,
  hrData,
  tbData,
  bvpData,
}: PlayerProfileProps) {
  const gameInfo = useMemo(() => parseGameString(game), [game]);

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        onClick={onClose}
        className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
        style={{
          animation: "fadeIn 0.3s ease-out",
        }}
      />

      {/* Modal */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto"
        style={{ animation: "fadeIn 0.3s ease-out" }}
      >
        <div
          className="w-full max-w-2xl rounded-2xl shadow-2xl"
          style={{
            background: "linear-gradient(145deg, rgba(45, 45, 55, 0.95) 0%, rgba(35, 35, 45, 0.98) 100%)",
            border: "1px solid var(--color-border-default)",
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between p-4 sm:p-6 border-b"
            style={{ borderColor: "var(--color-border-default)" }}
          >
            <div className="flex items-center gap-3 sm:gap-4 flex-1 min-w-0">
              {gameInfo && (
                <>
                  <img
                    src={getTeamLogoUrl(gameInfo.away)}
                    alt={gameInfo.away}
                    className="w-10 h-10 sm:w-12 sm:h-12 rounded-full flex-shrink-0"
                    style={{ border: "2px solid rgba(139, 92, 246, 0.3)" }}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "/default-logo.png";
                    }}
                  />
                  <div className="flex flex-col gap-1 min-w-0">
                    <h2 className="text-lg sm:text-2xl font-bold text-text-primary truncate">{playerName}</h2>
                    <div className="text-xs sm:text-sm text-text-secondary flex items-center gap-2">
                      <span className="truncate">{gameInfo.away}</span>
                      <span className="text-text-muted flex-shrink-0">@</span>
                      <span className="truncate">{gameInfo.home}</span>
                    </div>
                  </div>
                </>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-text-muted hover:text-text-primary text-xl sm:text-2xl transition-colors p-2 hover:bg-white/5 rounded-lg flex-shrink-0"
            >
              ✕
            </button>
          </div>

          {/* Content */}
          <div
            className="p-4 sm:p-6 overflow-y-auto"
            style={{
              maxHeight: "calc(100vh - 200px)",
              background: "rgba(30, 30, 40, 0.5)",
            }}
          >
            {/* Game Info Section */}
            {gameInfo && (
              <div
                className="mb-4 sm:mb-6 p-4 sm:p-5 rounded-xl border"
                style={{
                  background: "rgba(139, 92, 246, 0.08)",
                  borderColor: "var(--color-border-default)",
                }}
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-text-muted mb-1.5 font-semibold tracking-wide uppercase">📍 Matchup</div>
                    <div className="text-sm font-semibold text-text-primary">
                      {gameInfo.away} vs {gameInfo.home}
                    </div>
                  </div>
                  {hitsData?.Pitcher != null && (
                    <div>
                      <div className="text-xs text-text-muted mb-1.5 font-semibold tracking-wide uppercase">🤾 Opposing Pitcher</div>
                      <div className="text-sm font-semibold text-text-primary">
                        {String(hitsData.Pitcher)}
                      </div>
                    </div>
                  )}
                  {hitsData?.["O/U"] != null && (
                    <div>
                      <div className="text-xs text-text-muted mb-1.5 font-semibold tracking-wide uppercase">📊 O/U Book</div>
                      <div className="text-sm font-semibold text-text-primary">
                        {String(hitsData["O/U"])}
                      </div>
                    </div>
                  )}
                  {hitsData?.Odds != null && (
                    <div>
                      <div className="text-xs text-text-muted mb-1.5 font-semibold tracking-wide uppercase">💰 Odds</div>
                      <div className="text-sm font-semibold text-text-primary">
                        {String(hitsData.Odds)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Stats Grid */}
            <div>
              {hitsData && Object.keys(hitsData).length > 0 && (
                <StatGrid title="Hits Projection" stats={hitsData} icon="🎯" />
              )}
              {hrData && Object.keys(hrData).length > 0 && (
                <StatGrid title="HR Projection" stats={hrData} icon="💣" />
              )}
              {tbData && Object.keys(tbData).length > 0 && (
                <StatGrid title="Total Bases Projection" stats={tbData} icon="📊" />
              )}
              {bvpData && Object.keys(bvpData).length > 0 && (
                <StatGrid title="Batter vs Pitcher" stats={bvpData} icon="⚔️" />
              )}
            </div>

            {/* No Data */}
            {!hitsData && !hrData && !tbData && !bvpData && (
              <div className="text-center py-8">
                <div className="text-4xl mb-2">📭</div>
                <p className="text-text-muted">No stats available for this player</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div
            className="flex justify-end gap-3 p-4 sm:p-5 border-t"
            style={{ borderColor: "var(--color-border-default)" }}
          >
            <button
              onClick={onClose}
              className="px-6 py-2.5 rounded-xl font-medium transition-colors"
              style={{
                background: "var(--color-bg-card-hover)",
                color: "var(--color-text-primary)",
                border: "1px solid var(--color-border-default)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(139, 92, 246, 0.15)";
                e.currentTarget.style.borderColor = "rgba(139, 92, 246, 0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "var(--color-bg-card-hover)";
                e.currentTarget.style.borderColor = "var(--color-border-default)";
              }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
