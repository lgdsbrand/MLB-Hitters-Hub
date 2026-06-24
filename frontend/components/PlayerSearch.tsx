"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface Player {
  name: string;
  game: string;
  teams?: string;
  source?: string; // Track which data source this player came from
  stats?: Record<string, any>; // Include stats for preview
}

interface PlayerSearchProps {
  allPlayers: Player[];
  onPlayerSelect: (player: Player) => void;
}

export default function PlayerSearch({ allPlayers, onPlayerSelect }: PlayerSearchProps) {
  const [searchValue, setSearchValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const searchRef = useRef<HTMLDivElement>(null);

  // Get unique players and sort them
  const uniquePlayers = useMemo(() => {
    const seen = new Map<string, Player>();
    
    allPlayers.forEach((p) => {
      const key = p.name.toLowerCase();
      // Keep the player with the most complete data
      if (!seen.has(key) || (p.stats && Object.keys(p.stats).length > Object.keys(seen.get(key)!.stats || {}).length)) {
        seen.set(key, p);
      }
    });
    
    return Array.from(seen.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [allPlayers]);

  // Fuzzy matching function
  const fuzzyMatch = (text: string, query: string) => {
    const t = text.toLowerCase();
    const q = query.toLowerCase();
    
    if (t === q) return { score: 100, matched: true };
    if (t.startsWith(q)) return { score: 80, matched: true };
    if (t.includes(q)) return { score: 60, matched: true };
    
    // Fuzzy match: check if all characters from query appear in order
    let tIndex = 0;
    let qIndex = 0;
    let matches = 0;
    
    while (tIndex < t.length && qIndex < q.length) {
      if (t[tIndex] === q[qIndex]) {
        matches++;
        qIndex++;
      }
      tIndex++;
    }
    
    if (qIndex === q.length) {
      return { score: 40 + (matches / q.length) * 20, matched: true };
    }
    
    return { score: 0, matched: false };
  };

  // Filter suggestions based on search with intelligent matching
  const suggestions = useMemo(() => {
    if (!searchValue.trim()) return [];

    const query = searchValue.trim();

    const scored = uniquePlayers
      .map((p) => {
        const result = fuzzyMatch(p.name, query);
        return { ...p, score: result.score, matched: result.matched };
      })
      .filter((p) => p.matched)
      .sort((a, b) => b.score - a.score);

    return scored.slice(0, 15);
  }, [searchValue, uniquePlayers]);

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
        setSelectedIndex(-1);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || suggestions.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        handleSelectPlayer(suggestions[selectedIndex]);
      }
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }
  };

  const handleSelectPlayer = (player: Player) => {
    onPlayerSelect(player);
    setSearchValue("");
    setShowSuggestions(false);
    setSelectedIndex(-1);
  };

  // Highlight matched characters in suggestion
  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, i) => 
      regex.test(part) ? (
        <span key={i} className="text-accent-purple font-semibold">{part}</span>
      ) : (
        <span key={i}>{part}</span>
      )
    );
  };

  // Get stats preview for player
  const getStatsPreview = (player: Player) => {
    if (!player.stats) return null;
    
    const stats = [];
    if (player.stats.Pred) stats.push(`Pred: ${player.stats.Pred}`);
    if (player.stats.AVG) stats.push(`AVG: ${player.stats.AVG}`);
    if (player.stats.HR) stats.push(`HR: ${player.stats.HR}`);
    
    return stats.length > 0 ? stats.join(" • ") : null;
  };

  // Parse game string for team logos
  const parsedGame = useMemo(() => {
    if (!searchValue || suggestions.length === 0) return null;
    const game = suggestions[0]?.game;
    return game ? parseGameString(game) : null;
  }, [searchValue, suggestions]);

  return (
    <div ref={searchRef} className="relative w-full">
      <div className="relative">
        <input
          type="text"
          placeholder="🔍 Search players by name..."
          value={searchValue}
          onChange={(e) => {
            setSearchValue(e.target.value);
            setShowSuggestions(true);
            setSelectedIndex(-1);
          }}
          onFocus={(e) => {
            setShowSuggestions(true);
            e.target.style.borderColor = "var(--color-accent-purple)";
            e.target.style.boxShadow = "0 0 0 3px rgba(139, 92, 246, 0.1)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "var(--color-border-default)";
            e.target.style.boxShadow = "0 0 0 0 rgba(139, 92, 246, 0)";
          }}
          onKeyDown={handleKeyDown}
          className="w-full px-4 py-3 rounded-xl"
          style={{
            background: "var(--color-bg-input)",
            border: "1px solid var(--color-border-default)",
            color: "var(--color-text-primary)",
            fontSize: "15px",
            transition: "all 0.2s ease",
            boxShadow: "0 0 0 0 rgba(139, 92, 246, 0)",
          }}
        />
        {searchValue && (
          <button
            onClick={() => {
              setSearchValue("");
              setShowSuggestions(false);
              setSelectedIndex(-1);
            }}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-muted hover:text-accent-purple transition-colors"
            style={{ fontSize: "18px", lineHeight: 1 }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          className="absolute top-full left-0 right-0 mt-2 rounded-xl z-50 shadow-2xl animate-fade-in"
          style={{
            background: "var(--color-bg-card)",
            border: "1px solid var(--color-border-default)",
            maxHeight: "450px",
            overflowY: "auto",
          }}
        >
          <div className="px-3 py-2 border-b flex items-center justify-between" style={{ borderColor: "var(--color-border-subtle)" }}>
            <span className="text-xs text-text-muted font-medium">
              {suggestions.length} player{suggestions.length !== 1 ? "s" : ""} found
            </span>
            <span className="text-xs text-text-muted">Use ↑↓ to navigate, Enter to select</span>
          </div>
          {suggestions.map((player, idx) => {
            const parsed = player.game ? parseGameString(player.game) : null;
            const statsPreview = getStatsPreview(player);
            
            return (
              <button
                key={`${player.name}-${idx}`}
                onClick={() => handleSelectPlayer(player)}
                className={`w-full px-4 py-3 text-left hover:bg-bg-card-hover transition-colors border-b border-border-subtle last:border-b-0 flex items-center gap-3 group ${
                  idx === selectedIndex ? "bg-bg-card-hover" : ""
                }`}
                style={{
                  borderBottomColor: idx === suggestions.length - 1 ? "transparent" : "var(--color-border-subtle)",
                }}
              >
                {/* Team Logo */}
                {parsed && (
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {parsed.away && (
                      <img
                        src={getTeamLogoUrl(parsed.away)}
                        alt={parsed.away}
                        className="w-6 h-6 rounded-full"
                        style={{ width: 24, height: 24 }}
                        onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                      />
                    )}
                  </div>
                )}
                
                {/* Player Info */}
                <div className="flex flex-col gap-1 flex-1 min-w-0">
                  <div className="font-medium text-text-primary group-hover:text-accent-purple transition-colors flex items-center gap-2">
                    {player.score >= 80 && (
                      <span className="text-accent-green text-xs font-bold">★</span>
                    )}
                    <span className="truncate">
                      {highlightMatch(player.name, searchValue)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-text-muted">
                    {player.game && (
                      <span className="truncate">{player.game}</span>
                    )}
                    {statsPreview && (
                      <>
                        <span className="text-border-subtle">•</span>
                        <span className="text-accent-purple">{statsPreview}</span>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Arrow indicator */}
                <div className="text-accent-purple text-lg opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                  →
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* No Results */}
      {showSuggestions && searchValue && suggestions.length === 0 && (
        <div
          className="absolute top-full left-0 right-0 mt-2 rounded-xl z-50 p-6 text-center animate-fade-in"
          style={{
            background: "var(--color-bg-card)",
            border: "1px solid var(--color-border-default)",
          }}
        >
          <div className="text-3xl mb-2">🔍</div>
          <p className="text-text-muted text-sm font-medium">No players found</p>
          <p className="text-text-muted text-xs mt-1">Try a different search term or check spelling</p>
        </div>
      )}
    </div>
  );
}