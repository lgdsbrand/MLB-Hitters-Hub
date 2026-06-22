"use client";

import { useState, useEffect } from "react";
import { parseGameString, getTeamLogoUrl } from "@/lib/teamLogos";

interface Column {
  key: string;
  label: string;
  align?: "left" | "center" | "right";
}

interface DataTableProps {
  columns: Column[];
  data: Record<string, unknown>[];
  onAdd: (batter: string, game: string) => void;
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
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  useEffect(() => {
    setCurrentPage(1);
  }, [source, data.length]);

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

  const totalPages = Math.max(1, Math.ceil(data.length / itemsPerPage));
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentData = data.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="card-glass overflow-hidden">
      {/* Data count */}
      <div className="px-4 py-2 flex items-center justify-between" style={{ borderBottom: "1px solid var(--color-border-subtle)" }}>
        <span className="text-text-muted text-xs">
          {data.length} player{data.length !== 1 ? "s" : ""}
        </span>
        <span className="text-text-muted text-xs">
          Data updated: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ↻
        </span>
      </div>

      <div className="overflow-x-auto">
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
            {currentData.map((row, relativeIdx) => {
              const idx = startIndex + relativeIdx;
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
                      onClick={() => onAdd(batter, game)}
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
                            <span className="text-text-muted text-xs">@</span>
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

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-[var(--color-border-subtle)]">
          <span className="text-xs text-text-muted">
            Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, data.length)} of {data.length} records
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded bg-bg-secondary border border-border-subtle text-xs text-text-primary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-bg-card transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded bg-bg-secondary border border-border-subtle text-xs text-text-primary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-bg-card transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
