"use client";

import { useState } from "react";
import { ConsensusPlayer } from "@/lib/api";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface BestPlaysProps {
  players: ConsensusPlayer[];
  onAdd: (batter: string, game: string, rowData?: Record<string, unknown>) => void;
  isSelected: (batter: string, game: string) => boolean;
  onPlayerClick?: (playerName: string, game: string, rowData: Record<string, unknown>) => void;
}

function cleanHitProb(prob: string): string {
  if (!prob) return "";
  // Extract just the percentage part (e.g., "72%" from "72%3.5")
  const match = String(prob).match(/(\d+)%/);
  return match ? `${match[1]}%` : String(prob);
}

function getHitProbValue(prob: string): number {
  const match = String(prob).match(/(\d+)/);
  return match ? parseInt(match[1], 10) : 0;
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

function getScoreBadge(score: number): string {
  if (score >= 75) return "🟢";
  if (score >= 50) return "🟡";
  return "🔴";
}

function getScoreLabel(score: number): string {
  if (score >= 75) return "Excellent";
  if (score >= 50) return "Good";
  return "Fair";
}

function getEdgeLabel(score: number): string {
  if (score >= 75) return "Strong Edge";
  if (score >= 55) return "Good Edge";
  if (score >= 40) return "Moderate Edge";
  if (score >= 25) return "Slight Edge";
  return "Low Edge";
}

function getEdgeColor(score: number): string {
  if (score >= 75) return "#22c55e";
  if (score >= 55) return "#4ade80";
  if (score >= 40) return "#f59e0b";
  if (score >= 25) return "#f97316";
  return "#ef4444";
}

function getConfidenceLabel(prob: number): string {
  if (prob >= 65) return "High Confidence";
  if (prob >= 50) return "Moderate Confidence";
  if (prob >= 35) return "Fair Confidence";
  return "Low Confidence";
}

function getConfidenceClass(prob: number): string {
  if (prob >= 65) return "confidence-high";
  if (prob >= 50) return "confidence-moderate";
  if (prob >= 35) return "confidence-fair";
  return "confidence-low";
}

function getConfidenceBarColor(prob: number): string {
  if (prob >= 65) return "linear-gradient(90deg, #16a34a, #22c55e, #4ade80)";
  if (prob >= 50) return "linear-gradient(90deg, #d97706, #f59e0b, #fbbf24)";
  if (prob >= 35) return "linear-gradient(90deg, #ea580c, #f97316, #fb923c)";
  return "linear-gradient(90deg, #dc2626, #ef4444, #f87171)";
}

function getShortReasoning(player: ConsensusPlayer): string {
  const hitProb = parseFloat(String(player.HitProb || "0"));
  if (hitProb >= 75) return "Very high confidence in a hit today.";
  if (hitProb >= 65) return "Strong matchup and recent form boost.";
  if (hitProb >= 55) return "Favorable matchup with power upside.";
  if (hitProb >= 45) return "Solid plate discipline in this matchup.";
  return "Monitor for situational opportunities.";
}

function getAIReasoning(player: ConsensusPlayer): string {
  const hitProb = parseFloat(String(player.HitProb || "0"));

  let reasoning = "";

  // Build last 7 days summary if available
  let last7Summary = "";
  if (player.Last7H || player.Last7HR || player.Last7RBI) {
    const h = player.Last7H ? `${player.Last7H}H` : "";
    const r = player.Last7R ? `${player.Last7R}R` : "";
    const hr = player.Last7HR ? `${player.Last7HR}HR` : "";
    const rbi = player.Last7RBI ? `${player.Last7RBI}RBI` : "";
    const stats = [h, r, hr, rbi].filter(Boolean).join(", ");
    if (stats) {
      last7Summary = `In the last 7 days: ${stats}. `;
    }
  }

  // Generate primary reasoning based on hit probability
  if (hitProb >= 75) {
    reasoning = `${last7Summary}Very high confidence in a hit. ${player.Batter} has exceptional plate discipline and consistent performance against this opponent.`;
  } else if (hitProb >= 65) {
    reasoning = `${last7Summary}Strong statistical indicators suggest a high likelihood of recording a hit. Matchup dynamics favor this selection.`;
  } else if (hitProb >= 55) {
    reasoning = `${last7Summary}Moderate confidence based on recent performance trends and favorable matchup metrics. Historical data supports this play.`;
  } else if (hitProb >= 45) {
    reasoning = `${last7Summary}Balanced odds with some supporting statistics. Player has shown capability in similar situations.`;
  } else {
    reasoning = `${last7Summary}Lower confidence play. May warrant careful consideration alongside other factors.`;
  }

  // Add season/career stats if available
  if (player.BA && player.OPS) {
    reasoning += ` Season stats: ${player.BA} AVG, ${player.OPS} OPS.`;
  } else if (player.BA) {
    reasoning += ` Season batting average of ${player.BA} provides solid foundation for projection.`;
  } else if (player.OPS) {
    reasoning += ` OPS of ${player.OPS} indicates strong overall offensive performance.`;
  }

  return reasoning;
}

/* ──────────────────────────────────────────
   SVG Semicircular Gauge for Consensus Score
   ────────────────────────────────────────── */
function ConsensusGauge({ score, idx }: { score: number; idx: number }) {
  const clamped = Math.max(0, Math.min(100, score));
  const angleRad = Math.PI * (1 - clamped / 100);

  const cx = 50,
    cy = 52,
    r = 38,
    needleR = 30;

  // Needle endpoint
  const needleX = cx + needleR * Math.cos(angleRad);
  const needleY = cy - needleR * Math.sin(angleRad);

  // Filled arc endpoint
  const fillEndX = cx + r * Math.cos(angleRad);
  const fillEndY = cy - r * Math.sin(angleRad);

  const largeArc = clamped > 50 ? 1 : 0;
  const gradId = `gauge-grad-${idx}`;

  return (
    <svg viewBox="0 0 100 58" className="consensus-gauge-svg">
      <defs>
        <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#f97316" />
          <stop offset="40%" stopColor="#eab308" />
          <stop offset="100%" stopColor="#22c55e" />
        </linearGradient>
      </defs>
      {/* Background arc */}
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="7"
        strokeLinecap="round"
      />
      {/* Filled arc */}
      {clamped > 1 && (
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 ${largeArc} 1 ${fillEndX.toFixed(2)} ${fillEndY.toFixed(2)}`}
          fill="none"
          stroke={`url(#${gradId})`}
          strokeWidth="7"
          strokeLinecap="round"
        />
      )}
      {/* Needle */}
      <line
        x1={cx}
        y1={cy}
        x2={Number(needleX.toFixed(2))}
        y2={Number(needleY.toFixed(2))}
        stroke="#e2e8f0"
        strokeWidth="2"
        strokeLinecap="round"
      />
      {/* Center dot */}
      <circle cx={cx} cy={cy} r="3" fill="#e2e8f0" />
    </svg>
  );
}

interface BestPlayCardProps {
  player: ConsensusPlayer;
  idx: number;
  onAdd: BestPlaysProps["onAdd"];
  isSelected: BestPlaysProps["isSelected"];
  onPlayerClick?: BestPlaysProps["onPlayerClick"];
}

function BestPlayCard({ player, idx, onAdd, isSelected, onPlayerClick }: BestPlayCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const parsed = parseGameString(player.Game || "");
  const added = isSelected(player.Batter, player.Game);

  const consensusScore = parseFloat(String(player.Consensus || "0"));
  const hitProbValue = getHitProbValue(player.HitProb);

  // Format batting average to 3 digits
  const formatBA = (ba: string | number | undefined): string => {
    if (!ba) return "";
    const baStr = String(ba);
    if (baStr.includes(".")) return baStr;
    return (parseFloat(String(ba)) / 1000).toFixed(3);
  };

  // Format OPS to 3 decimal places
  const formatOPS = (ops: string | number | undefined): string => {
    if (!ops) return "";
    const opsNum = parseFloat(String(ops));
    if (isNaN(opsNum)) return String(ops);
    return opsNum.toFixed(3);
  };

  return (
    <div
      className="spotlight-card animate-fade-in"
      style={{ animationDelay: `${idx * 0.1}s` }}
    >
      {/* ── Header: Rank + Player + Add ── */}
      <div className="spotlight-card-header">
        <div className="flex items-center gap-3">
          <span className={`rank-badge rank-${idx + 1}`}>{idx + 1}</span>
          <div>
            <button
              onClick={() => onPlayerClick && onPlayerClick(player.Batter, player.Game, player as Record<string, unknown>)}
              className="spotlight-player-name hover:text-accent-purple transition-colors cursor-pointer"
            >
              {player.Batter}
            </button>
            <div className="spotlight-game-info">
              {parsed &&
                (() => {
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
              <span>{player.Game.replace(" @ ", " vs ")}</span>
            </div>
          </div>
        </div>

        <button
          className={`btn-add ${added ? "added" : ""}`}
          onClick={() =>
            onAdd(
              player.Batter,
              player.Game,
              player as Record<string, unknown>
            )
          }
          title={added ? "Added to bet sheet" : "Add to bet sheet"}
        >
          {added ? "✓" : "+"}
        </button>
      </div>

      {/* ── Scores Section: Gauge + Probability ── */}
      <div className="spotlight-scores">
        {/* Consensus Score */}
        <div className="spotlight-score-section">
          <div className="spotlight-score-label">
            Consensus Score{" "}
            <span className="spotlight-info-icon" title="Combined model consensus score out of 100">ⓘ</span>
          </div>
          <div className="spotlight-gauge-row">
            <ConsensusGauge score={consensusScore} idx={idx} />
            <span className="spotlight-score-value">{player.Consensus}</span>
          </div>
          <div
            className="spotlight-edge-label"
            style={{ color: getEdgeColor(consensusScore) }}
          >
            {getEdgeLabel(consensusScore)}
          </div>
        </div>

        {/* Hit Probability */}
        <div className="spotlight-score-section spotlight-prob-section">
          <div className="spotlight-score-label">
            Hit Probability{" "}
            <span className="spotlight-info-icon" title="AI-predicted probability of recording a hit">ⓘ</span>
          </div>
          <div className="spotlight-prob-row">
            <span className="spotlight-prob-value">
              {cleanHitProb(player.HitProb)}
            </span>
          </div>
          {/* Confidence Bar */}
          <div className="confidence-bar-track">
            <div
              className="confidence-bar-fill"
              style={{
                width: `${Math.min(hitProbValue, 100)}%`,
                background: getConfidenceBarColor(hitProbValue),
              }}
            />
          </div>
          {/* Confidence Pill */}
          <div className={`confidence-pill ${getConfidenceClass(hitProbValue)}`}>
            {getConfidenceLabel(hitProbValue)}
          </div>
        </div>
      </div>

      {/* ── Stats Row ── */}
      {player.BA && player.BA !== "" && (
        <div className="spotlight-stats-row">
          <div className="spotlight-stat">
            <div className="spotlight-stat-label">BA</div>
            <div className="spotlight-stat-value">{formatBA(player.BA)}</div>
          </div>
          <div className="spotlight-stat">
            <div className="spotlight-stat-label">OPS</div>
            <div className="spotlight-stat-value">{formatOPS(player.OPS)}</div>
          </div>
          <div className="spotlight-stat">
            <div className="spotlight-stat-label">vs</div>
            <div className="spotlight-stat-value spotlight-stat-pitcher">
              {player.Pitcher}
            </div>
          </div>
        </div>
      )}

      {/* ── AI Reasoning Section ── */}
      <div className="spotlight-ai-section">
        <button
          onClick={() => setIsExpanded((prev) => !prev)}
          className="spotlight-ai-toggle"
        >
          <div className="spotlight-ai-left">
            <span className="spotlight-ai-icon">🤖</span>
            <div>
              <span className="spotlight-ai-label">AI REASONING</span>
              {!isExpanded && (
                <span className="spotlight-ai-summary">
                  {getShortReasoning(player)}
                </span>
              )}
            </div>
          </div>
          <span
            className="spotlight-ai-chevron"
            style={{
              transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
            }}
          >
            ❯
          </span>
        </button>

        {isExpanded && (
          <div className="spotlight-ai-content">
            {/* Main Reasoning */}
            <div className="spotlight-ai-reasoning-text">
              {getAIReasoning(player)}
            </div>

            {/* Score Breakdown */}
            <div className="spotlight-ai-factors">
              <div className="spotlight-ai-factors-title">📊 Factor Scores:</div>
              <div className="spotlight-ai-factors-grid">
                <div>
                  <div className="spotlight-ai-factor-row">
                    {getScoreBadge(player.HitScore || 0)} Hit Prediction
                  </div>
                  <div className="spotlight-ai-factor-detail">
                    {(player.HitScore || 0).toFixed(0)}/100{" "}
                    {getScoreLabel(player.HitScore || 0)}
                  </div>
                </div>
                <div>
                  <div className="spotlight-ai-factor-row">
                    {getScoreBadge(player.BvPScore || 0)} vs Pitcher
                  </div>
                  <div className="spotlight-ai-factor-detail">
                    {(player.BvPScore || 0).toFixed(0)}/100{" "}
                    {getScoreLabel(player.BvPScore || 0)}
                  </div>
                </div>
                <div>
                  <div className="spotlight-ai-factor-row">
                    {getScoreBadge(player.TrendScore || 0)} Hit Trend
                  </div>
                  <div className="spotlight-ai-factor-detail">
                    {(player.TrendScore || 0).toFixed(0)}/100{" "}
                    {getScoreLabel(player.TrendScore || 0)}
                  </div>
                </div>
              </div>
            </div>

            {/* Last 7 Days Stats */}
            {(player.Last7H || player.Last7AVG || player.Last7OPS) && (
              <div className="spotlight-ai-last7">
                <div className="spotlight-ai-factors-title">📈 Last 7 Days:</div>
                <div className="spotlight-ai-last7-stats">
                  {player.Last7H && <span>🎯 {player.Last7H}H</span>}
                  {player.Last7R && <span>🏃 {player.Last7R}R</span>}
                  {player.Last7HR && <span>⚾ {player.Last7HR}HR</span>}
                  {player.Last7RBI && <span>📍 {player.Last7RBI}RBI</span>}
                  {player.Last7AVG && <span>AVG: {player.Last7AVG}</span>}
                  {player.Last7OPS && <span>OPS: {player.Last7OPS}</span>}
                </div>
              </div>
            )}

            {/* Vs Pitcher Stats */}
            {(player.BvPBA || player.BvPOPS) && (
              <div className="spotlight-ai-bvp">
                <div className="spotlight-ai-factors-title">
                  ⚔️ vs {player.Pitcher}:
                </div>
                <div className="spotlight-ai-last7-stats">
                  {player.BvPBA && <span>BA: {player.BvPBA}</span>}
                  {player.BvPOPS && <span>OPS: {player.BvPOPS}</span>}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function BestPlays({
  players,
  onAdd,
  isSelected,
  onPlayerClick,
}: BestPlaysProps) {
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
            onPlayerClick={onPlayerClick}
          />
        ))}
      </div>
    </div>
  );
}
