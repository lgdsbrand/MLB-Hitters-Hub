"use client";

interface TabBarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const TABS = [
  { id: "last7", label: "Last 7 Days", shortLabel: "Last 7" },
  { id: "last15", label: "Last 15 Days", shortLabel: "Last 15" },
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

      {/* Mobile: Horizontal Scrollable Buttons */}
      <div className="sm:hidden flex items-center gap-2 overflow-x-auto pb-2" style={{ scrollbarWidth: "thin" }}>
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex-shrink-0 px-3 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
              activeTab === tab.id
                ? "bg-accent-green text-bg-primary shadow-lg shadow-accent-green/30"
                : "bg-bg-card border border-border-default text-text-primary hover:border-accent-green hover:text-accent-green"
            }`}
          >
            {tab.shortLabel}
          </button>
        ))}
      </div>
    </>
  );
}
