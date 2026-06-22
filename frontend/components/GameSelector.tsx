"use client";

import { getTeamLogoUrl, parseGameString, getTeamName } from "@/lib/teamLogos";

interface GameSelectorProps {
  games: string[];
  selectedGame: string | null;
  onSelect: (game: string | null) => void;
}

export default function GameSelector({
  games,
  selectedGame,
  onSelect,
}: GameSelectorProps) {
  return (
    <div className="flex items-center gap-3">
      <label className="text-text-secondary text-sm font-medium uppercase tracking-wider">
        Select Game
      </label>
      <div className="relative">
        <select
          className="game-select min-w-[200px]"
          value={selectedGame || "All Games"}
          onChange={(e) => {
            const val = e.target.value;
            onSelect(val === "All Games" ? null : val);
          }}
        >
          <option value="All Games">All Games</option>
          {games.map((game) => {
            const parsed = parseGameString(game);
            const label = parsed
              ? `${getTeamName(parsed.away)} @ ${getTeamName(parsed.home)}`
              : game;
            return (
              <option key={game} value={game}>
                {label}
              </option>
            );
          })}
        </select>
      </div>
      {/* Show team logos for selected game */}
      {selectedGame && (() => {
        const parsed = parseGameString(selectedGame);
        if (!parsed) return null;
        return (
          <div className="flex items-center gap-2 ml-2">
            <img
              src={getTeamLogoUrl(parsed.away)}
              alt={parsed.away}
              className="team-logo"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
            <span className="text-text-muted text-xs">@</span>
            <img
              src={getTeamLogoUrl(parsed.home)}
              alt={parsed.home}
              className="team-logo"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
          </div>
        );
      })()}
    </div>
  );
}
