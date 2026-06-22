"use client";

import { useState, useRef, useEffect } from "react";
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
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedGameLabel = selectedGame
    ? (() => {
        const parsed = parseGameString(selectedGame);
        return parsed
          ? `${getTeamName(parsed.away)} @ ${getTeamName(parsed.home)}`
          : selectedGame;
      })()
    : "All Games";

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="flex items-center gap-3">
      <label className="text-text-secondary text-sm font-medium uppercase tracking-wider">
        Select Game
      </label>
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-bg-card border border-border-default hover:border-accent-purple transition-colors text-text-primary text-sm font-medium min-w-[220px] text-left"
        >
          <span className="flex-1 truncate">{selectedGameLabel}</span>
          <svg
            className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </button>

        {/* Dropdown Menu */}
        {isOpen && (
          <div className="absolute top-full left-0 mt-2 w-full bg-bg-card border border-border-default rounded-lg shadow-lg z-50 max-h-[400px] overflow-y-auto table-scroll-container">
            {/* All Games Option */}
            <button
              onClick={() => {
                onSelect(null);
                setIsOpen(false);
              }}
              className={`w-full px-4 py-3 text-left text-sm transition-colors hover:bg-bg-card-hover border-b border-border-subtle flex items-center gap-2 ${
                !selectedGame ? "bg-bg-card-hover text-accent-purple" : "text-text-primary"
              }`}
            >
              <span>All Games</span>
            </button>

            {/* Game Options */}
            {games.map((game) => {
              const parsed = parseGameString(game);
              if (!parsed) return null;

              const label = `${getTeamName(parsed.away)} @ ${getTeamName(parsed.home)}`;
              const isSelected = selectedGame === game;

              return (
                <button
                  key={game}
                  onClick={() => {
                    onSelect(game);
                    setIsOpen(false);
                  }}
                  className={`w-full px-4 py-3 text-left text-sm transition-colors hover:bg-bg-card-hover border-b border-border-subtle flex items-center gap-3 ${
                    isSelected ? "bg-bg-card-hover text-accent-purple" : "text-text-primary"
                  }`}
                >
                  {/* Away Team Logo */}
                  <img
                    src={getTeamLogoUrl(parsed.away)}
                    alt={parsed.away}
                    className="w-6 h-6 object-contain flex-shrink-0"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                  />
                  <span className="flex-1 truncate">{label}</span>
                  {/* Home Team Logo */}
                  <img
                    src={getTeamLogoUrl(parsed.home)}
                    alt={parsed.home}
                    className="w-6 h-6 object-contain flex-shrink-0"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                  />
                </button>
              );
            })}
          </div>
        )}
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
