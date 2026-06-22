"use client";

import { useState } from "react";
import DataTable from "./DataTable";
import { ClubPlayer } from "@/lib/api";

interface ClubSectionProps {
  hitsData: ClubPlayer[];
  tbData: ClubPlayer[];
  streakData: ClubPlayer[];
  onAdd: (batter: string, game: string, rowData?: Record<string, unknown>) => void;
  isSelected: (batter: string, game: string) => boolean;
}

export default function ClubSection({
  hitsData,
  tbData,
  streakData,
  onAdd,
  isSelected,
}: ClubSectionProps) {
  const [activeTab, setActiveTab] = useState<"hits" | "tb" | "streak">("hits");

  const getColumns = () => {
    if (activeTab === "hits") {
      return [
        { key: "Batter", label: "Batter" },
        { key: "Game", label: "Game" },
        { key: "Pred", label: "Prob" },
        { key: "O/U", label: "O/U" },
        { key: "Record", label: "Record", align: "center" as const },
      ];
    }
    if (activeTab === "tb") {
      return [
        { key: "Batter", label: "Batter" },
        { key: "Game", label: "Game" },
        { key: "TB Pred", label: "Prob" },
        { key: "Line", label: "Line" },
        { key: "Record", label: "Record", align: "center" as const },
      ];
    }
    return [
      { key: "Batter", label: "Batter" },
      { key: "Game", label: "Game" },
      { key: "Pred", label: "Prob" },
      { key: "Streak", label: "Streak", align: "center" as const },
    ];
  };

  const getData = () => {
    if (activeTab === "hits") return hitsData;
    if (activeTab === "tb") return tbData;
    return streakData;
  };

  return (
    <div className="mt-8 mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <span className="text-accent-gold">🏆</span> 
          {activeTab === "streak" ? "5-Day Hit Streak Club" : "100% Club"}
        </h2>
        <div className="flex bg-bg-card rounded-lg p-1 border border-border-default">
          <button
            onClick={() => setActiveTab("hits")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === "hits" ? "bg-accent-green text-bg-primary" : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Hits
          </button>
          <button
            onClick={() => setActiveTab("tb")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === "tb" ? "bg-accent-green text-bg-primary" : "text-text-secondary hover:text-text-primary"
            }`}
          >
            Total Bases
          </button>
          <button
            onClick={() => setActiveTab("streak")}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === "streak" ? "bg-accent-green text-bg-primary" : "text-text-secondary hover:text-text-primary"
            }`}
          >
            5-Day Streak
          </button>
        </div>
      </div>
      
      <DataTable
        columns={getColumns()}
        data={getData()}
        onAdd={onAdd}
        isSelected={isSelected}
        source={activeTab}
        emptyMessage={`No players qualify for the ${activeTab === "streak" ? "5-Day Hit Streak" : "100%"} Club today.`}
      />
    </div>
  );
}
