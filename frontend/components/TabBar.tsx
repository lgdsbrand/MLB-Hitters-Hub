"use client";

interface TabBarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const TABS = [
  { id: "last7", label: "Last 7 Days Hot Hitters" },
  { id: "hits", label: "Hit Predictions" },
  { id: "hr", label: "HR Predictions" },
  { id: "tb", label: "TB Predictions" },
  { id: "bvp", label: "BvP Matchup" },
];

export default function TabBar({ activeTab, onTabChange }: TabBarProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: "none" }}>
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
  );
}
