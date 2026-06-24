"use client";

import { useState, useEffect, useCallback } from "react";

export interface BetSelection {
  id: string;
  batter: string;
  game: string;
  source: string; // which tab they were added from
  prop: string; // "Hit", "Total Bases", "HRR" (Hits, Runs, RBIs)
  odds: string | number;
  probability: string | number; // AI score / prediction
  addedAt: string;
}

interface StoredBetSheet {
  date: string;
  selections: BetSelection[];
}

const STORAGE_KEY = "mlb_hitters_hub_betsheet";

function getTodayStr(): string {
  // Get current date in Eastern Time
  const now = new Date();
  const easternDate = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const year = easternDate.getFullYear();
  const month = String(easternDate.getMonth() + 1).padStart(2, "0");
  const day = String(easternDate.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`; // YYYY-MM-DD in Eastern Time
}

function loadFromStorage(): BetSelection[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: StoredBetSheet = JSON.parse(raw);
    // Midnight reset: if stored date differs from today, clear
    if (parsed.date !== getTodayStr()) {
      localStorage.removeItem(STORAGE_KEY);
      return [];
    }
    return parsed.selections || [];
  } catch {
    return [];
  }
}

function saveToStorage(selections: BetSelection[]): void {
  if (typeof window === "undefined") return;
  const data: StoredBetSheet = {
    date: getTodayStr(),
    selections,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

export function useBetSheet() {
  const [selections, setSelections] = useState<BetSelection[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // Load on mount
  useEffect(() => {
    setSelections(loadFromStorage());
  }, []);

  // Save whenever selections change
  useEffect(() => {
    saveToStorage(selections);
  }, [selections]);

  const addPlayer = useCallback(
    (
      batter: string,
      game: string,
      source: string,
      prop: string = "Hit",
      odds: string | number = "-",
      probability: string | number = "-"
    ) => {
      setSelections((prev) => {
        // Prevent duplicates by batter + game
        const id = `${batter}__${game}`;
        if (prev.some((s) => s.id === id)) return prev;
        return [
          ...prev,
          {
            id,
            batter,
            game,
            source,
            prop,
            odds,
            probability,
            addedAt: new Date().toLocaleTimeString(),
          },
        ];
      });
    },
    []
  );

  const removePlayer = useCallback((id: string) => {
    setSelections((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setSelections([]);
  }, []);

  const isSelected = useCallback(
    (batter: string, game: string): boolean => {
      const id = `${batter}__${game}`;
      return selections.some((s) => s.id === id);
    },
    [selections]
  );

  const toggleSheet = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  return {
    selections,
    isOpen,
    addPlayer,
    removePlayer,
    clearAll,
    isSelected,
    toggleSheet,
    setIsOpen,
    count: selections.length,
  };
}
