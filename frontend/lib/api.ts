/**
 * API client for MLB Hitters Hub backend.
 * All endpoints proxy through Next.js rewrites to FastAPI at :8000.
 */

const BASE = process.env.NODE_ENV === "production" ? "/_/backend/api/hitters" : "/api/hitters";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    let errorMsg = res.statusText || "Unknown Error";
    try {
      const errorData = await res.json();
      errorMsg = errorData.detail 
        ? (typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)) 
        : JSON.stringify(errorData);
    } catch {
      const textData = await res.text().catch(() => "");
      if (textData) {
        errorMsg = textData;
      }
    }
    throw new Error(`API error: ${res.status} - ${errorMsg}`);
  }
  return res.json();
}

function gameParam(game?: string | null): string {
  if (!game || game === "All Games") return "";
  return `?game=${encodeURIComponent(game)}`;
}

// --- Response types ---

export interface ApiResponse<T> {
  data: T[];
  count: number;
}

export interface HitPrediction {
  Batter: string;
  Pitcher: string;
  Game: string;
  Pred: string;
  "O/U": string | number;
  Odds: string;
  AB: string;
  H: string;
  HR: string;
  BA: string;
  OBP: string;
  OPS: string;
  [key: string]: unknown;
}

export interface HRPrediction {
  Batter: string;
  Pitcher: string;
  Game: string;
  "HR Pred": string;
  Odds: string;
  AB: string;
  H: string;
  HR: string;
  BA: string;
  OBP: string;
  OPS: string;
  [key: string]: unknown;
}

export interface TBPrediction {
  Batter: string;
  Pitcher: string;
  Game: string;
  "TB Pred": string | number;
  Line: string | number;
  Over: string;
  AB: string;
  H: string;
  HR: string;
  BA: string;
  OBP: string;
  OPS: string;
  [key: string]: unknown;
}

export interface BvPData {
  Batter: string;
  Icon: string;
  Pitcher: string;
  Game: string;
  qAB: string;
  "HH%": string;
  AB: string;
  H: string;
  "2B/3B": string;
  HR: string;
  BB: string;
  BA: string;
  OBP: string;
  OPS: string;
  [key: string]: unknown;
}

export interface Last7Hitter {
  Name: string;
  Team: string;
  G: string | number;
  PA: string | number;
  AB: string | number;
  R: string | number;
  H: string | number;
  HR: string | number;
  RBI: string | number;
  AVG: string | number;
  OBP: string | number;
  SLG: string | number;
  OPS: string | number;
  [key: string]: unknown;
}

export interface ConsensusPlayer {
  Batter: string;
  Pitcher: string;
  Game: string;
  Consensus: number;
  HitProb: string;
  Trend: string;
  AB: string;
  H: string;
  BA: string;
  OPS: string;
  [key: string]: unknown;
}

export interface ClubPlayer {
  Batter: string;
  Pitcher: string;
  Game: string;
  Pred?: string;
  "TB Pred"?: string;
  "O/U"?: string | number;
  Line?: string | number;
  Record?: string;
  Streak?: string;
  Trend: string;
  AB: string;
  H: string;
  BA: string;
  OBP: string;
  OPS: string;
  [key: string]: unknown;
}

// --- API functions ---

export async function fetchGames(): Promise<string[]> {
  const res = await fetchJSON<{ games: string[] }>(`${BASE}/games`);
  return res.games;
}

export async function fetchHits(game?: string | null): Promise<HitPrediction[]> {
  const res = await fetchJSON<ApiResponse<HitPrediction>>(`${BASE}/hits${gameParam(game)}`);
  return res.data;
}

export async function fetchHR(game?: string | null): Promise<HRPrediction[]> {
  const res = await fetchJSON<ApiResponse<HRPrediction>>(`${BASE}/hr${gameParam(game)}`);
  return res.data;
}

export async function fetchTB(game?: string | null): Promise<TBPrediction[]> {
  const res = await fetchJSON<ApiResponse<TBPrediction>>(`${BASE}/tb${gameParam(game)}`);
  return res.data;
}

export async function fetchBvP(game?: string | null): Promise<BvPData[]> {
  const res = await fetchJSON<ApiResponse<BvPData>>(`${BASE}/bvp${gameParam(game)}`);
  return res.data;
}

export async function fetchLast7(): Promise<Last7Hitter[]> {
  const res = await fetchJSON<ApiResponse<Last7Hitter>>(`${BASE}/last7`);
  return res.data;
}

export async function fetchConsensus(game?: string | null): Promise<ConsensusPlayer[]> {
  const res = await fetchJSON<ApiResponse<ConsensusPlayer>>(`${BASE}/consensus${gameParam(game)}`);
  return res.data;
}

export async function fetchClubHits(game?: string | null): Promise<ClubPlayer[]> {
  const res = await fetchJSON<ApiResponse<ClubPlayer>>(`${BASE}/club/hits${gameParam(game)}`);
  return res.data;
}

export async function fetchClubTB(game?: string | null): Promise<ClubPlayer[]> {
  const res = await fetchJSON<ApiResponse<ClubPlayer>>(`${BASE}/club/tb${gameParam(game)}`);
  return res.data;
}

export async function fetchStreak(game?: string | null): Promise<ClubPlayer[]> {
  const res = await fetchJSON<ApiResponse<ClubPlayer>>(`${BASE}/streak${gameParam(game)}`);
  return res.data;
}
