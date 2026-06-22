"use client";

import { useState } from "react";

interface TabBarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const TABS = [
  { id: "last7", label: "Last 7 Days Hot Hitters", shortLabel: "Last 7" },
  { id: "hits", label: "Hit Predictions", shortLabel: "Hits" },
  { id: "hr", label: "HR Predictions", shortLabel: "HR" },
  { id: "tb", label: "TB Predictions", shortLabel: "TB" },
  { id: "bvp", label: "BvP Matchup", shortLabel: "BvP" },
];

export default function TabBar({ activeTab, onTabChange }: TabBarProps) {
  return (
    <>
      {/* Desktop: Tab Pills */}
      <div className="hidden sm:flex items-center gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: "none" }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-pill ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Mobile: Dropdown */}
      <select
        value={activeTab}
        onChange={(e) => onTabChange(e.target.value)}
        className="sm:hidden table-select"
        style={{
          width: "100%",
          padding: "10px 14px",
          borderRadius: "8px",
          border: "1px solid var(--color-border-default)",
          background: "var(--color-bg-input)",
          color: "var(--color-text-primary)",
          fontSize: "0.9rem",
          fontWeight: 500,
          cursor: "pointer",
          appearance: "none",
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238b5cf6' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`,
          backgroundRepeat: "no-repeat",
          backgroundPosition: "right 12px center",
          paddingRight: "36px",
        }}
      >
        {TABS.map((tab) => (
          <option key={tab.id} value={tab.id}>
            {tab.label}
          </option>
        ))}
      </select>
    </>
  );
}
