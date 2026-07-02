"use client";

import { useState, useEffect } from "react";
import {
  fetchGames,
  fetchHits,
  fetchHR,
  fetchTB,
  fetchBvP,
  fetchLast7,
  fetchLast15,
  fetchConsensus,
  fetchClubHits,
  fetchClubTB,
  fetchStreak,
  fetchHitStreaks,
  HitPrediction,
  HRPrediction,
  TBPrediction,
  BvPData,
  Last7Hitter,
  ConsensusPlayer,
  ClubPlayer,
  HitStreak,
} from "@/lib/api";

export function useHittersData(selectedGame: string | null) {
  const [games, setGames] = useState<string[]>([]);
  const [loadingGames, setLoadingGames] = useState(true);

  // Tab Data
  const [hitsData, setHitsData] = useState<HitPrediction[]>([]);
  const [hrData, setHrData] = useState<HRPrediction[]>([]);
  const [tbData, setTbData] = useState<TBPrediction[]>([]);
  const [bvpData, setBvpData] = useState<BvPData[]>([]);
  const [last7Data, setLast7Data] = useState<Last7Hitter[]>([]);
  const [last15Data, setLast15Data] = useState<Last7Hitter[]>([]);

  // Hero & Club Data
  const [consensusData, setConsensusData] = useState<ConsensusPlayer[]>([]);
  const [clubHits, setClubHits] = useState<ClubPlayer[]>([]);
  const [clubTB, setClubTB] = useState<ClubPlayer[]>([]);
  const [streakData, setStreakData] = useState<ClubPlayer[]>([]);

  const [loading, setLoading] = useState(false);

  // Fetch unique games once
  useEffect(() => {
    async function loadGames() {
      try {
        const list = await fetchGames();
        setGames(list);
      } catch (err) {
        console.error("Failed to load games", err);
      } finally {
        setLoadingGames(false);
      }
    }
    loadGames();
  }, []);

  // Fetch all other data when game changes
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [
          hits,
          hr,
          tb,
          bvp,
          last7,
          last15,
          consensus,
          cHits,
          cTB,
          streak,
        ] = await Promise.all([
          fetchHits(selectedGame),
          fetchHR(selectedGame),
          fetchTB(selectedGame),
          fetchBvP(selectedGame),
          fetchLast7(),
          fetchLast15(),
          fetchConsensus(selectedGame),
          fetchClubHits(selectedGame),
          fetchClubTB(selectedGame),
          fetchStreak(selectedGame),
        ]);

        setHitsData(hits);
        setHrData(hr);
        setTbData(tb);
        setBvpData(bvp);
        setLast7Data(last7);
        setLast15Data(last15);
        setConsensusData(consensus);
        setClubHits(cHits);
        setClubTB(cTB);
        setStreakData(streak);
      } catch (err) {
        console.error("Failed to load data", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [selectedGame]);

  return {
    games,
    loadingGames,
    loading,
    hitsData,
    hrData,
    tbData,
    bvpData,
    last7Data,
    last15Data,
    consensusData,
    clubHits,
    clubTB,
    streakData,
  };
}
