"use client";

import { useState, useEffect } from "react";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface Column {
  key: string;
  label: string;
  align?: "left" | "center" | "right";
  sortable?: boolean;
}

// SVG arrow primitives — all rendered at a consistent size and colored via `color` prop
function ArrowUp({ color }: { color: string }) {
  return (
    <svg width="11" height="13" viewBox="0 0 11 13" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M5.5 1L5.5 12M5.5 1L1 5.5M5.5 1L10 5.5" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function ArrowDown({ color }: { color: string }) {
  return (
    <svg width="11" height="13" viewBox="0 0 11 13" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M5.5 12L5.5 1M5.5 12L1 7.5M5.5 12L10 7.5" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function ArrowRight({ color }: { color: string }) {
  return (
    <svg width="13" height="11" viewBox="0 0 13 11" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M1 5.5H12M12 5.5L7.5 1M12 5.5L7.5 10" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function ArrowUpRight({ color }: { color: string }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 10L10 2M10 2H4M10 2V8" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function ArrowDownRight({ color }: { color: string }) {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M2 2L10 10M10 10H4M10 10V4" stroke={color} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

// Each trend maps to: label, background color, and an array of arrow components to render
interface TrendConfig {
  label: string;
  color: string;
  bgColor: string;
  arrows: React.ReactNode;
}

function getTrendDisplay(trend: string) {
  const C = {
    green:      "#10b981",
    lightGreen: "#34d399",
    orange:     "#f97316",
    yellow:     "#eab308",
    red:        "#ef4444",
    darkRed:    "#dc2626",
  };
  const BG = {
    green:      "rgba(16, 185, 129, 0.1)",
    lightGreen: "rgba(52, 211, 153, 0.1)",
    orange:     "rgba(249, 115, 22, 0.1)",
    yellow:     "rgba(234, 179, 8, 0.1)",
    red:        "rgba(239, 68, 68, 0.1)",
    darkRed:    "rgba(220, 38, 38, 0.1)",
  };

  const trendMap: Record<string, TrendConfig> = {
    // ── Pure up ──────────────────────────────────────────────
    "^^": {
      label: "Strong Up", color: C.green, bgColor: BG.green,
      arrows: <><ArrowUp color={C.green}/><ArrowUp color={C.green}/></>,
    },
    "^": {
      label: "Up", color: C.lightGreen, bgColor: BG.lightGreen,
      arrows: <ArrowUp color={C.lightGreen}/>,
    },
    // ── Pure down ────────────────────────────────────────────
    "vv": {
      label: "Strong Down", color: C.darkRed, bgColor: BG.darkRed,
      arrows: <><ArrowDown color={C.darkRed}/><ArrowDown color={C.darkRed}/></>,
    },
    "v": {
      label: "Down", color: C.red, bgColor: BG.red,
      arrows: <ArrowDown color={C.red}/>,
    },
    // ── Pure neutral ─────────────────────────────────────────
    ">>": {
      label: "Steady Neutral", color: C.yellow, bgColor: BG.yellow,
      arrows: <><ArrowRight color={C.yellow}/><ArrowRight color={C.yellow}/></>,
    },
    ">": {
      label: "Neutral", color: C.yellow, bgColor: BG.yellow,
      arrows: <ArrowRight color={C.yellow}/>,
    },
    // ── Up + mix ─────────────────────────────────────────────
    "^v": {
      label: "Up Then Down", color: C.orange, bgColor: BG.orange,
      arrows: <><ArrowUpRight color={C.orange}/><ArrowDownRight color={C.orange}/></>,
    },
    "^>": {
      label: "Up Then Neutral", color: C.orange, bgColor: BG.orange,
      arrows: <><ArrowUp color={C.orange}/><ArrowRight color={C.orange}/></>,
    },
    // ── Down + mix ───────────────────────────────────────────
    "v^": {
      label: "Down Then Up", color: C.orange, bgColor: BG.orange,
      arrows: <><ArrowDownRight color={C.orange}/><ArrowUpRight color={C.orange}/></>,
    },
    "v>": {
      label: "Down Then Neutral", color: C.orange, bgColor: BG.orange,
      arrows: <><ArrowDown color={C.orange}/><ArrowRight color={C.orange}/></>,
    },
    // ── Neutral + mix ────────────────────────────────────────
    ">^": {
      label: "Neutral Then Up", color: C.orange, bgColor: BG.orange,
      arrows: <><ArrowRight color={C.orange}/><ArrowUp color={C.orange}/></>,
    },
    ">v": {
      label: "Neutral Then Down", color: C.orange, bgColor: BG.orange,
      arrows: <><ArrowRight color={C.orange}/><ArrowDown color={C.orange}/></>,
    },
  };

  const trendInfo = trendMap[trend] ?? {
    label: trend,
    color: C.orange,
    bgColor: BG.orange,
    arrows: <ArrowRight color={C.orange}/>,
  };

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "2px",
        padding: "4px 7px",
        borderRadius: "6px",
        backgroundColor: trendInfo.bgColor,
        minWidth: "32px",
      }}
      title={trendInfo.label}
    >
      {trendInfo.arrows}
    </div>
  );
}

interface DataTableProps {
  columns: Column[];
  data: Record<string, unknown>[];
  onAdd: (batter: string, game: string, rowData?: Record<string, unknown>) => void;
  isSelected: (batter: string, game: string) => boolean;
  source: string;
  loading?: boolean;
  emptyMessage?: string;
  batterKey?: string;
  gameKey?: string;
  onPlayerClick?: (playerName: string, game: string, rowData: Record<string, unknown>) => void;
}

export default function DataTable({
  columns,
  data,
  onAdd,
  isSelected,
  source,
  loading = false,
  emptyMessage = "No data available",
  batterKey = "Batter",
  gameKey = "Game",
  onPlayerClick,
}: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // Reset sort state when source changes so each table's sorting is independent
  useEffect(() => {
    setSortColumn(null);
    setSortDirection("asc");
  }, [source]);

  const handleSort = (columnKey: string, isSortable: boolean) => {
    if (!isSortable) return;

    if (sortColumn === columnKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(columnKey);
      setSortDirection("asc");
    }
  };

  const getSortedData = () => {
    if (!sortColumn) return data;

    const sorted = [...data].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const aNum = parseFloat(String(aVal));
      const bNum = parseFloat(String(bVal));

      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDirection === "asc" ? aNum - bNum : bNum - aNum;
      }

      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();

      if (sortDirection === "asc") {
        return aStr.localeCompare(bStr);
      } else {
        return bStr.localeCompare(aStr);
      }
    });

    return sorted;
  };

  // Determine if sorting should be enabled based on source
  const isSortingEnabled = ["last7", "last15", "bvp", "hits", "tb"].includes(source);

  if (loading) {
    return (
      <div className="card-glass p-8 text-center">
        <div className="inline-block w-6 h-6 border-2 border-accent-green border-t-transparent rounded-full animate-spin" />
        <p className="text-text-secondary mt-3 text-sm">Loading data...</p>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="card-glass p-8 text-center">
        <p className="text-text-secondary text-sm">{emptyMessage}</p>
      </div>
    );
  }

  const currentData = getSortedData();

  return (
    <div className="card-glass">
      {/* Data count */}
      <div className="px-4 py-2 flex items-center justify-between" style={{ borderBottom: "1px solid var(--color-border-subtle)" }}>
        <span className="text-text-muted text-xs">
          {data.length} player{data.length !== 1 ? "s" : ""}
        </span>
        <span className="text-text-muted text-xs">
          Data updated: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ↻
        </span>
      </div>

      <div className="table-scroll-container">
        <table className={`data-table data-table-${source}`}>
          <thead>
            <tr>
              <th></th>
              <th>#</th>
              {columns.map((col) => {
                const isSortable = isSortingEnabled && col.sortable !== false;
                const isActive = sortColumn === col.key;
                const sortArrow = isActive ? (sortDirection === "asc" ? "↑" : "↓") : "—";

                return (
                  <th
                    key={col.key}
                    style={{ textAlign: col.align || "left" }}
                    className={isSortable ? "cursor-pointer hover:bg-bg-card transition-colors" : ""}
                    onClick={() => handleSort(col.key, isSortable)}
                  >
                    <div className="flex items-center gap-1.5">
                      <span>{col.label}</span>
                      {isSortable && (
                        <span
                          style={{
                            fontSize: "10px",
                            opacity: isActive ? 1 : 0.3,
                            fontWeight: isActive ? 600 : 400,
                            color: isActive ? "var(--color-accent-green)" : "inherit",
                            minWidth: "12px",
                          }}
                        >
                          {sortArrow}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {currentData.map((row, idx) => {
              const batter = String(row[batterKey] || "");
              const game = String(row[gameKey] || "");
              const added = isSelected(batter, game);
              const parsed = parseGameString(game);

              return (
                <tr key={`${batter}-${game}-${idx}`}>
                  {/* Add button */}
                  <td>
                    <button
                      className={`btn-add ${added ? "added" : ""}`}
                      onClick={() => onAdd(batter, game, row)}
                      title={added ? "Added" : "Add to bet sheet"}
                    >
                      {added ? "✓" : "+"}
                    </button>
                  </td>
                  {/* Rank */}
                  <td>
                    <span className="text-text-muted font-medium text-xs">{idx + 1}</span>
                  </td>
                  {/* Data columns */}
                  {columns.map((col) => {
                    const val = row[col.key];
                    const display = val === null || val === undefined ? "" : String(val);

                    // Special rendering for player name - make it clickable
                    if ((col.key === batterKey || col.key === "player_name" || col.key === "Batter" || col.key === "Name") && onPlayerClick) {
                      const playerName = display;
                      const game = String(row[gameKey] || row["Game"] || row["team"] || "");
                      return (
                        <td
                          key={col.key}
                          style={{ textAlign: col.align || "left" }}
                          className="cursor-pointer"
                        >
                          <button
                            onClick={() => onPlayerClick(playerName, game, row)}
                            className="text-text-primary hover:text-accent-purple transition-colors font-medium hover:underline text-left"
                          >
                            {playerName}
                          </button>
                        </td>
                      );
                    }

                    // Special rendering for game column — show logos
                    if (col.key === gameKey && parsed) {
                      const awayUrl = getTeamLogoUrl(parsed.away);
                      const homeUrl = getTeamLogoUrl(parsed.home);
                      return (
                        <td key={col.key} style={{ textAlign: col.align || "left" }}>
                          <div className="flex items-center gap-1.5">
                            {awayUrl && (
                              <img
                                src={awayUrl}
                                alt=""
                                className="team-logo"
                                style={{ width: 18, height: 18 }}
                                onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                              />
                            )}
                            <span className="text-text-muted text-xs">vs</span>
                            {homeUrl && (
                              <img
                                src={homeUrl}
                                alt=""
                                className="team-logo"
                                style={{ width: 18, height: 18 }}
                                onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                              />
                            )}
                            <span className="ml-1 text-xs text-text-secondary">{display.replace(" @ ", " vs ")}</span>
                          </div>
                        </td>
                      );
                    }

                    // Special rendering for trend column (Icon)
                    if (col.key === "Icon") {
                      return (
                        <td key={col.key} style={{ textAlign: col.align || "center", padding: "8px 4px" }}>
                          {getTrendDisplay(display)}
                        </td>
                      );
                    }

                    // Highlight prediction percentages
                    const isPredCol = col.key === "Pred" || col.key === "HR Pred" || col.key === "TB Pred";
                    
                    // Clean prediction columns to show only percentage
                    let cleanDisplay = display;
                    if (isPredCol && display) {
                      const match = String(display).match(/(\d+)%/);
                      cleanDisplay = match ? `${match[1]}%` : display;
                    }
                    
                    const isPredHigh = isPredCol && parseFloat(cleanDisplay) >= 65;

                    return (
                      <td
                        key={col.key}
                        style={{
                          textAlign: col.align || "left",
                          color: isPredHigh ? "var(--color-accent-green)" : undefined,
                          fontWeight: isPredHigh ? 600 : undefined,
                        }}
                      >
                        {cleanDisplay}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}