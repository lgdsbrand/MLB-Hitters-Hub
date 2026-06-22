"use client";

import { ConsensusPlayer } from "@/lib/api";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface BestPlaysProps {
  players: ConsensusPlayer[];
  onAdd: (batter: string, game: string) => void;
  isSelected: (batter: string, game: string) => boolean;
}

function getFireEmojis(prob: string): string {
  const val = parseFloat(prob);
  if (isNaN(val)) return "";
  if (val >= 75) return "🔥🔥🔥🔥🔥";
  if (val >= 65) return "🔥🔥🔥🔥";
  if (val >= 55) return "🔥🔥🔥";
  if (val >= 45) return "🔥🔥";
  if (val >= 30) return "🔥";
  return "";
}

export default function BestPlays({ players, onAdd, isSelected }: BestPlaysProps) {
  const top3 = players.slice(0, 3);

  if (top3.length === 0) {
    return (
      <div className="card-glass p-8 text-center">
        <p className="text-text-secondary">Loading best plays...</p>
      </div>
    );
  }

  return (
    <div className="card-glass p-6">
      <h2
        className="text-center mb-6"
        style={{
          fontFamily: "Georgia, 'Times New Roman', serif",
          fontStyle: "italic",
          fontSize: "1.5rem",
          color: "var(--color-text-primary)",
        }}
      >
        Best Plays of the Day
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {top3.map((player, idx) => {
          const parsed = parseGameString(player.Game || "");
          const added = isSelected(player.Batter, player.Game);

          return (
            <div
              key={player.Batter + player.Game}
              className="relative p-5 rounded-xl animate-fade-in"
              style={{
                animationDelay: `${idx * 0.1}s`,
                background:
                  "linear-gradient(135deg, rgba(28, 35, 51, 0.8), rgba(13, 17, 23, 0.9))",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              {/* Rank badge */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className={`rank-badge rank-${idx + 1}`}>
                    {idx + 1}
                  </span>
                  <div>
                    <div className="font-bold text-sm text-text-primary">
                      {player.Batter}
                    </div>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      {parsed && (
                        <img
                          src={getTeamLogoUrl(parsed.away)}
                          alt=""
                          className="team-logo"
                          style={{ width: 16, height: 16 }}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                          }}
                        />
                      )}
                      <span className="text-text-muted text-xs">
                        {player.Game}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Add button */}
                <button
                  className={`btn-add ${added ? "added" : ""}`}
                  onClick={() => onAdd(player.Batter, player.Game)}
                  title={added ? "Added to bet sheet" : "Add to bet sheet"}
                >
                  {added ? "✓" : "+"}
                </button>
              </div>

              {/* Scores row */}
              <div className="flex items-center justify-between mt-4">
                <div>
                  <div className="text-text-muted text-xs uppercase tracking-wider mb-1">
                    Consensus Score
                  </div>
                  <span className="consensus-badge">{player.Consensus}</span>
                </div>
                <div className="text-right">
                  <div className="text-text-muted text-xs uppercase tracking-wider mb-1">
                    Hit Probability
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-lg text-text-primary">
                      {player.HitProb}
                    </span>
                    <span className="text-sm">
                      {getFireEmojis(player.HitProb)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Stats */}
              {player.BA && player.BA !== "" && (
                <div className="flex gap-4 mt-3 pt-3" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                  <div className="text-xs">
                    <span className="text-text-muted">BA </span>
                    <span className="text-text-primary font-medium">{player.BA}</span>
                  </div>
                  <div className="text-xs">
                    <span className="text-text-muted">OPS </span>
                    <span className="text-text-primary font-medium">{player.OPS}</span>
                  </div>
                  <div className="text-xs">
                    <span className="text-text-muted">vs </span>
                    <span className="text-text-secondary font-medium">{player.Pitcher}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
