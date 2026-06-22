"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import GameSelector from "@/components/GameSelector";
import BestPlays from "@/components/BestPlays";
import TabBar from "@/components/TabBar";
import DataTable from "@/components/DataTable";
import ClubSection from "@/components/ClubSection";
import HitStreaksTable from "@/components/HitStreaksTable";
import { useHittersData } from "@/hooks/useHittersData";
import { useBetSheet } from "@/hooks/useBetSheet";

export default function Home() {
  const [selectedGame, setSelectedGame] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("hits");
  const tableRef = useRef<HTMLDivElement>(null);

  const {
    games,
    loading,
    hitsData,
    hrData,
    tbData,
    bvpData,
    last7Data,
    consensusData,
    clubHits,
    clubTB,
    streakData,
    hitStreaksData,
  } = useHittersData(selectedGame);

  const betSheet = useBetSheet();

  const handleAddPlayer = (batter: string, game: string, rowData?: Record<string, unknown>) => {
    let sourceName = "Hits";
    let prop = "Hit";
    let odds = "-";
    let probability = "-";

    if (rowData) {
      switch (activeTab) {
        case "hr":
          sourceName = "HR";
          prop = "HR";
          odds = String(rowData["Odds"] || "-");
          probability = String(rowData["HR Pred"] || "-");
          break;
        case "tb":
          sourceName = "TB";
          prop = "Total Bases";
          odds = String(rowData["Over"] || "-");
          probability = String(rowData["TB Pred"] || "-");
          break;
        case "bvp":
          sourceName = "BvP";
          prop = "Hit";
          odds = String(rowData["HH%"] || "-");
          probability = String(rowData["Icon"] || "-");
          break;
        case "last7":
          sourceName = "Last 7";
          prop = "HRR"; // Hits, Runs, RBIs
          odds = "-";
          probability = "-";
          break;
        case "hits":
        default:
          sourceName = "Hits";
          prop = "Hit";
          odds = String(rowData["Odds"] || "-");
          probability = String(rowData["Pred"] || "-");
      }
    } else {
      if (activeTab === "hr") sourceName = "HR";
      if (activeTab === "tb") sourceName = "TB";
      if (activeTab === "bvp") sourceName = "BvP";
      if (activeTab === "last7") sourceName = "Last 7";
    }
    
    // Special handling for consensus data (BestPlays)
    if (rowData && "Consensus" in rowData) {
      sourceName = "Consensus";
      prop = "Hit";
      odds = "-";
      probability = String(rowData["HitProb"] || rowData["Consensus"] || "-");
    }
    
    betSheet.addPlayer(batter, game, sourceName, prop, odds, probability);
  };

  const getTableColumns = () => {
    switch (activeTab) {
      case "last7":
        return [
          { key: "Name", label: "Player" },
          { key: "Team", label: "Team" },
          { key: "AVG", label: "AVG" },
          { key: "H", label: "Hits" },
          { key: "RBI", label: "RBI" },
          { key: "OPS", label: "OPS" },
        ];
      case "hr":
        return [
          { key: "Batter", label: "Batter" },
          { key: "Pitcher", label: "Pitcher" },
          { key: "Game", label: "Game" },
          { key: "HR Pred", label: "HR Pred" },
          { key: "Odds", label: "Odds" },
          { key: "AB", label: "AB" },
          { key: "H", label: "H" },
          { key: "HR", label: "HR" },
          { key: "BA", label: "BA" },
          { key: "OPS", label: "OPS" },
        ];
      case "tb":
        return [
          { key: "Batter", label: "Batter" },
          { key: "Pitcher", label: "Pitcher" },
          { key: "Game", label: "Game" },
          { key: "TB Pred", label: "TB Pred" },
          { key: "Line", label: "Line" },
          { key: "Over", label: "Over" },
          { key: "AB", label: "AB" },
          { key: "H", label: "H" },
          { key: "BA", label: "BA" },
          { key: "OPS", label: "OPS" },
        ];
      case "bvp":
        return [
          { key: "Batter", label: "Batter" },
          { key: "Icon", label: "Trend" },
          { key: "Pitcher", label: "Pitcher" },
          { key: "Game", label: "Game" },
          { key: "qAB", label: "qAB" },
          { key: "HH%", label: "HH%" },
          { key: "AB", label: "AB" },
          { key: "H", label: "H" },
          { key: "2B/3B", label: "2B/3B" },
          { key: "HR", label: "HR" },
          { key: "BA", label: "BA" },
          { key: "OPS", label: "OPS" },
        ];
      case "hits":
      default:
        return [
          { key: "Batter", label: "Batter" },
          { key: "Pitcher", label: "Pitcher" },
          { key: "Game", label: "Game" },
          { key: "Pred", label: "Pred" },
          { key: "O/U", label: "O/U" },
          { key: "Odds", label: "Odds" },
          { key: "AB", label: "AB" },
          { key: "H", label: "H" },
          { key: "BA", label: "BA" },
          { key: "OPS", label: "OPS" },
        ];
    }
  };

  const getTableData = () => {
    switch (activeTab) {
      case "last7": return last7Data;
      case "hr": return hrData;
      case "tb": return tbData;
      case "bvp": return bvpData;
      case "hits":
      default: return hitsData;
    }
  };

  return (
    <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <header className="flex flex-col sm:flex-row items-center justify-between gap-6 mb-10">
        <div className="flex flex-col items-center sm:items-start">
          <div className="text-accent-teal text-xs tracking-[0.2em] uppercase font-bold mb-1">
            Powered By
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-text-primary">
            MLB Hitters Hub
          </h1>
        </div>
        
        <div className="flex items-center gap-6">
          <Link
            href="/betsheet"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-bg-card border border-border-default hover:border-accent-green transition-colors text-text-primary text-sm font-medium relative"
          >
            <span>Bet Sheet</span>
            {betSheet.count > 0 && (
              <span className="bg-accent-green text-bg-primary text-xs font-bold w-5 h-5 flex items-center justify-center rounded-full">
                {betSheet.count}
              </span>
            )}
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <BestPlays
        players={consensusData}
        onAdd={handleAddPlayer}
        isSelected={betSheet.isSelected}
      />

      {/* Clubs & Streaks */}
      <ClubSection
        hitsData={clubHits}
        tbData={clubTB}
        streakData={streakData}
        onAdd={handleAddPlayer}
        isSelected={betSheet.isSelected}
      />

      {/* Hit Streaks Table */}
      <HitStreaksTable data={hitStreaksData} loading={loading} />

      {/* Main Data View */}
      <div className="mt-8 mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4" ref={tableRef}>
        <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
        <GameSelector
          games={games}
          selectedGame={selectedGame}
          onSelect={setSelectedGame}
        />
      </div>

      <DataTable
        columns={getTableColumns()}
        data={getTableData() as Record<string, unknown>[]}
        onAdd={handleAddPlayer}
        isSelected={betSheet.isSelected}
        source={activeTab}
        loading={loading}
        batterKey={activeTab === "last7" ? "Name" : "Batter"}
      />

      {/* Info Panel */}
      <div className="mt-12 info-panel flex flex-col md:flex-row items-center gap-8">
        <div className="flex items-start gap-4 flex-1">
          <div className="text-3xl">💡</div>
          <div>
            <h3 className="font-bold text-lg mb-2 text-text-primary uppercase tracking-wide">
              About Consensus Score
            </h3>
            <p className="text-text-secondary text-sm mb-4">
              Our Consensus Score (0-100) combines four key factors to identify the strongest overall hitter edge for today:
            </p>
            <div className="grid grid-cols-2 gap-y-2 gap-x-8 text-sm">
              <div className="flex items-center gap-2 text-text-primary">
                <span className="text-accent-green">✓</span> Last 7 Day Performance
              </div>
              <div className="flex items-center gap-2 text-text-primary">
                <span className="text-accent-green">✓</span> Hit Probability Rank
              </div>
              <div className="flex items-center gap-2 text-text-primary">
                <span className="text-accent-green">✓</span> Hit Prediction Rank
              </div>
              <div className="flex items-center gap-2 text-text-primary">
                <span className="text-accent-green">✓</span> Batter vs Pitcher Rank
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-bg-primary p-6 rounded-xl border border-border-default flex flex-col items-center justify-center min-w-[200px]">
          <div className="text-text-muted text-xs uppercase tracking-wider mb-2 font-bold">
            Score Range
          </div>
          <div className="score-range">0-100</div>
          <div className="text-center mt-3 text-sm text-text-secondary italic">
            Higher scores = <br/> Stronger overall hitter edge
          </div>
        </div>
      </div>


    </main>
  );
}
