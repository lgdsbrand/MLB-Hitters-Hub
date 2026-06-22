"use client";

import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface Column {
  key: string;
  label: string;
  align?: "left" | "center" | "right";
}

function getTrendDisplay(trend: string) {
  const trendMap: Record<string, { label: string; color: string; bgColor: string; svg: string }> = {
    "^^": {
      label: "Strong Up",
      color: "#10b981",
      bgColor: "rgba(16, 185, 129, 0.1)",
      svg: "↑↑",
    },
    "^": {
      label: "Up",
      color: "#34d399",
      bgColor: "rgba(52, 211, 153, 0.1)",
      svg: "↑",
    },
    "^v": {
      label: "Up Then Down",
      color: "#f97316",
      bgColor: "rgba(249, 115, 22, 0.1)",
      svg: "↗↘",
    },
    ">v": {
      label: "Mixed",
      color: "#f97316",
      bgColor: "rgba(249, 115, 22, 0.1)",
      svg: "↗",
    },
    ">": {
      label: "Neutral",
      color: "#eab308",
      bgColor: "rgba(234, 179, 8, 0.1)",
      svg: "→",
    },
    "v>": {
      label: "Mixed Down",
      color: "#f97316",
      bgColor: "rgba(249, 115, 22, 0.1)",
      svg: "↘",
    },
    "v^": {
      label: "Down Then Up",
      color: "#f97316",
      bgColor: "rgba(249, 115, 22, 0.1)",
      svg: "↘↗",
    },
    "v": {
      label: "Down",
      color: "#ef4444",
      bgColor: "rgba(239, 68, 68, 0.1)",
      svg: "↓",
    },
    "vv": {
      label: "Strong Down",
      color: "#dc2626",
      bgColor: "rgba(220, 38, 38, 0.1)",
      svg: "↓↓",
    },
  };

  const trendInfo = trendMap[trend] || { label: trend, color: "#9ca3af", bgColor: "rgba(156, 163, 175, 0.1)", svg: trend };

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "4px 8px",
        borderRadius: "6px",
        backgroundColor: trendInfo.bgColor,
        minWidth: "32px",
        fontSize: "14px",
        fontWeight: "600",
        color: trendInfo.color,
        letterSpacing: "0.5px",
      }}
      title={trendInfo.label}
    >
      {trendInfo.svg}
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
}: DataTableProps) {

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

  const currentData = data;

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
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 40 }}></th>
              <th style={{ width: 28 }}>#</th>
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{ textAlign: col.align || "left" }}
                >
                  {col.label}
                </th>
              ))}
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

                    // Special rendering for game column — show logos
                    if (col.key === gameKey && parsed) {
                      return (
                        <td key={col.key} style={{ textAlign: col.align || "left" }}>
                          <div className="flex items-center gap-1.5">
                            <img
                              src={getTeamLogoUrl(parsed.away)}
                              alt=""
                              className="team-logo"
                              style={{ width: 18, height: 18 }}
                              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                            />
                            <span className="text-text-muted text-xs">vs</span>
                            <img
                              src={getTeamLogoUrl(parsed.home)}
                              alt=""
                              className="team-logo"
                              style={{ width: 18, height: 18 }}
                              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                            />
                            <span className="ml-1 text-xs text-text-secondary">{display}</span>
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
                    const isPredCol = col.key === "Pred" || col.key === "HR Pred";
                    const isPredHigh = isPredCol && parseFloat(display) >= 65;

                    return (
                      <td
                        key={col.key}
                        style={{
                          textAlign: col.align || "left",
                          color: isPredHigh ? "var(--color-accent-green)" : undefined,
                          fontWeight: isPredHigh ? 600 : undefined,
                        }}
                      >
                        {display}
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
