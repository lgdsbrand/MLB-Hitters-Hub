"use client";

import { useRef, useEffect } from "react";
import { getTeamLogoUrl, parseGameString } from "@/lib/teamLogos";

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
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll selected game into view
  useEffect(() => {
    if (selectedGame && scrollContainerRef.current) {
      const selectedButton = scrollContainerRef.current.querySelector('[data-selected="true"]');
      if (selectedButton) {
        selectedButton.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "nearest" });
      }
    }
  }, [selectedGame]);

  return (
    <div className="flex flex-col gap-2">
      <label className="text-text-secondary text-sm font-medium uppercase tracking-wider px-1">
        Select Game
      </label>
      <div 
        ref={scrollContainerRef}
        className="flex items-center gap-2 overflow-x-auto pb-2"
        style={{ scrollbarWidth: "thin", scrollPaddingRight: "8px" }}
      >
        {/* All Games Option */}
        <button
          onClick={() => onSelect(null)}
          data-selected={!selectedGame ? "true" : "false"}
          className={`flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
            !selectedGame
              ? "bg-accent-green text-bg-primary shadow-lg shadow-accent-green/30"
              : "bg-bg-card border border-border-default text-text-primary hover:border-accent-green hover:text-accent-green"
          }`}
        >
          All Games
        </button>

        {/* Game Options */}
        {games.map((game) => {
          const parsed = parseGameString(game);
          if (!parsed) return null;

          const isSelected = selectedGame === game;

          return (
            <button
              key={game}
              onClick={() => onSelect(game)}
              data-selected={isSelected ? "true" : "false"}
              className={`flex-shrink-0 flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                isSelected
                  ? "bg-accent-green text-bg-primary shadow-lg shadow-accent-green/30"
                  : "bg-bg-card border border-border-default text-text-primary hover:border-accent-green hover:text-accent-green"
              }`}
            >
              {/* Away Team Logo */}
              <img
                src={getTeamLogoUrl(parsed.away)}
                alt={parsed.away}
                className="w-5 h-5 object-contain flex-shrink-0"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
              <span className="text-xs">vs</span>
              {/* Home Team Logo */}
              <img
                src={getTeamLogoUrl(parsed.home)}
                alt={parsed.home}
                className="w-5 h-5 object-contain flex-shrink-0"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
