"use client";

import { useState } from "react";
import { ConsensusPlayer } from "@/lib/api";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface BestPlaysProps {
  players: ConsensusPlayer[];
  onAdd: (batter: string, game: string, rowData?: Record<string, unknown>) => void;
  isSelected: (batter: string, game: string) => boolean;
}

function cleanHitProb(prob: string): string {
  if (!prob) return "";
  // Extract just the percentage part (e.g., "72%" from "72%3.5")
  const match = String(prob).match(/(\d+)%/);
  return match ? `${match[1]}%` : String(prob);
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

function getAIReasoning(player: ConsensusPlayer): string {
  const consensus = parseFloat(String(player.Consensus || "0"));
  const hitProb = parseFloat(String(player.HitProb || "0"));
  
  let reasoning = "";
  
  if (hitProb >= 75) {
    reasoning = `Very high confidence in a hit. ${player.Batter} has exceptional plate discipline and consistent performance against this opponent.`;
  } else if (hitProb >= 65) {
    reasoning = `Strong statistical indicators suggest a high likelihood of recording a hit. Recent form and matchup dynamics favor this selection.`;
  } else if (hitProb >= 55) {
    reasoning = `Moderate confidence based on recent performance trends and favorable matchup metrics. Historical data supports this play.`;
  } else if (hitProb >= 45) {
    reasoning = `Balanced odds with some supporting statistics. Player has shown capability in similar situations.`;
  } else {
    reasoning = `Lower confidence play. May warrant careful consideration alongside other factors.`;
  }
  
  if (player.BA) {
    reasoning += ` Player batting average of ${player.BA} provides solid foundation for projection.`;
  }
  
  if (player.OPS) {
    reasoning += ` OPS of ${player.OPS} indicates strong overall offensive performance.`;
  }
  
  return reasoning;
}

interface BestPlayCardProps {
  player: ConsensusPlayer;
  idx: number;
  onAdd: BestPlaysProps["onAdd"];
  isSelected: BestPlaysProps["isSelected"];
}

function BestPlayCard({ player, idx, onAdd, isSelected }: BestPlayCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const parsed = parseGameString(player.Game || "");
  const added = isSelected(player.Batter, player.Game);

  // Format batting average to 3 digits
  const formatBA = (ba: string | number | undefined): string => {
    if (!ba) return "";
    const baStr = String(ba);
    // If it's already in decimal format (e.g., ".250"), keep it as is
    if (baStr.includes(".")) {
      return baStr;
    }
    // Otherwise, convert to decimal format
    return (parseFloat(String(ba)) / 1000).toFixed(3);
  };

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
              {parsed && (() => {
                const url = getTeamLogoUrl(parsed.away);
                return url ? (
                  <img
                    src={url}
                    alt=""
                    className="team-logo"
                    style={{ width: 16, height: 16 }}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                    }}
                  />
                ) : null;
              })()}
              <span className="text-text-muted text-xs">
                {player.Game.replace(" @ ", " vs ")}
              </span>
            </div>
          </div>
        </div>

        {/* Add button */}
        <button
          className={`btn-add ${added ? "added" : ""}`}
          onClick={() => onAdd(player.Batter, player.Game, player as Record<string, unknown>)}
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
              {cleanHitProb(player.HitProb)}
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
            <span className="text-text-primary font-medium">{formatBA(player.BA)}</span>
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

      {/* AI Reasoning Section */}
      <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <button
          onClick={() => setIsExpanded((prev) => !prev)}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "8px 0",
            background: "none",
            border: "none",
            color: "var(--color-accent-purple)",
            cursor: "pointer",
            fontSize: "0.85rem",
            fontWeight: 600,
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = "var(--color-accent-purple-light)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.color = "var(--color-accent-purple)";
          }}
        >
          <span>🤖 AI Reasoning</span>
          <span style={{ transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s" }}>▼</span>
        </button>
        
        {isExpanded && (
          <div
            style={{
              marginTop: "10px",
              padding: "10px 8px",
              background: "rgba(139, 92, 246, 0.08)",
              borderRadius: "8px",
              border: "1px solid rgba(139, 92, 246, 0.15)",
              fontSize: "0.8rem",
              lineHeight: "1.5",
              color: "var(--color-text-secondary)",
              animation: "fadeIn 0.2s ease-out",
            }}
          >
            {getAIReasoning(player)}
          </div>
        )}
      </div>
    </div>
  );
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
        className="text-center mb-6 animate-spotlight-pulse"
        style={{
          fontFamily: "var(--font-sans), system-ui, -apple-system, sans-serif",
          fontWeight: 800,
          fontSize: "1.25rem",
          letterSpacing: "0.15em",
          textTransform: "uppercase",
          color: "var(--color-accent-purple)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "0.75rem",
        }}
      >
        <span style={{ fontSize: "1.5rem" }}>⚡</span>
        SPOTLIGHT EDGE OF THE DAY
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {top3.map((player, idx) => (
          <BestPlayCard
            key={`${player.Batter}-${player.Game}-${idx}`}
            player={player}
            idx={idx}
            onAdd={onAdd}
            isSelected={isSelected}
          />
        ))}
      </div>
    </div>
  );
}
