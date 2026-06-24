"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface Player {
  name: string;
  game: string;
  teams?: string;
}

interface PlayerSearchProps {
  allPlayers: Player[];
  onPlayerSelect: (player: Player) => void;
}

export default function PlayerSearch({ allPlayers, onPlayerSelect }: PlayerSearchProps) {
  const [searchValue, setSearchValue] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Get unique players and sort them
  const uniquePlayers = useMemo(() => {
    const seen = new Set<string>();
    return allPlayers
      .filter((p) => {
        if (seen.has(p.name)) return false;
        seen.add(p.name);
        return true;
      })
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [allPlayers]);

  // Filter suggestions based on search with intelligent matching
  const suggestions = useMemo(() => {
    if (!searchValue.trim()) return [];

    const query = searchValue.toLowerCase();
    const queryLength = query.length;

    return uniquePlayers
      .filter((p) => {
        const playerName = p.name.toLowerCase();
        
        // Priority 1: First character match
        if (playerName.startsWith(query)) {
          return true;
        }
        
        // Priority 2: Contains query anywhere
        if (playerName.includes(query)) {
          return true;
        }
        
        return false;
      })
      .sort((a, b) => {
        const aName = a.name.toLowerCase();
        const bName = b.name.toLowerCase();
        
        // Sort by: first character match > contains > alphabetical
        const aStarts = aName.startsWith(query);
        const bStarts = bName.startsWith(query);
        
        if (aStarts && !bStarts) return -1;
        if (!aStarts && bStarts) return 1;
        
        return aName.localeCompare(bName);
      })
      .slice(0, 10);
  }, [searchValue, uniquePlayers]);

  // Close suggestions on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelectPlayer = (player: Player) => {
    onPlayerSelect(player);
    setSearchValue("");
    setShowSuggestions(false);
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
          }}
          onFocus={() => setShowSuggestions(true)}
          className="w-full px-4 py-3 rounded-xl"
          style={{
            background: "var(--color-bg-input)",
            border: "1px solid var(--color-border-default)",
            color: "var(--color-text-primary)",
            fontSize: "15px",
            transition: "all 0.2s ease",
            boxShadow: "0 0 0 0 rgba(139, 92, 246, 0)",
          }}
          onFocus={(e) => {
            e.target.style.borderColor = "var(--color-accent-purple)";
            e.target.style.boxShadow = "0 0 0 3px rgba(139, 92, 246, 0.1)";
          }}
          onBlur={(e) => {
            e.target.style.borderColor = "var(--color-border-default)";
            e.target.style.boxShadow = "0 0 0 0 rgba(139, 92, 246, 0)";
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") {
              setShowSuggestions(false);
            }
          }}
        />
        {searchValue && (
          <button
            onClick={() => {
              setSearchValue("");
              setShowSuggestions(false);
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
            maxHeight: "400px",
            overflowY: "auto",
          }}
        >
          <div className="px-3 py-2 border-b" style={{ borderColor: "var(--color-border-subtle)" }}>
            <span className="text-xs text-text-muted font-medium">
              {suggestions.length} player{suggestions.length !== 1 ? "s" : ""} found
            </span>
          </div>
          {suggestions.map((player, idx) => {
            const startsWithQuery = player.name.toLowerCase().startsWith(searchValue.toLowerCase());
            return (
              <button
                key={`${player.name}-${idx}`}
                onClick={() => handleSelectPlayer(player)}
                className="w-full px-4 py-3 text-left hover:bg-bg-card-hover transition-colors border-b border-border-subtle last:border-b-0 flex items-center justify-between group"
                style={{
                  borderBottomColor: idx === suggestions.length - 1 ? "transparent" : "var(--color-border-subtle)",
                }}
              >
                <div className="flex flex-col gap-1 flex-1 min-w-0">
                  <div className="font-medium text-text-primary group-hover:text-accent-purple transition-colors flex items-center gap-2">
                    {startsWithQuery && (
                      <span className="text-accent-green text-xs font-bold">★</span>
                    )}
                    <span className="truncate">
                      {highlightMatch(player.name, searchValue)}
                    </span>
                  </div>
                  {player.game && (
                    <div className="text-xs text-text-muted truncate">{player.game}</div>
                  )}
                </div>
                <div className="text-accent-purple text-lg opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 ml-2">
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
          <p className="text-text-muted text-xs mt-1">Try a different search term</p>
        </div>
      )}
    </div>
  );
}
