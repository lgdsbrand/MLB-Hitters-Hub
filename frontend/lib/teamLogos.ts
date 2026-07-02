/**
 * MLB team abbreviation mapping.
 * Maps CSV abbreviations to ESPN CDN team codes and display names.
 */

export interface TeamInfo {
  espnAbbr: string;
  name: string;
  city: string;
}

// CSV abbreviation → { ESPN abbreviation, full name, city }
export const TEAM_MAP: Record<string, TeamInfo> = {
  ANA: { espnAbbr: "laa", name: "Angels", city: "Los Angeles" },
  LAA: { espnAbbr: "laa", name: "Angels", city: "Los Angeles" },
  ATH: { espnAbbr: "oak", name: "Athletics", city: "Oakland" },
  OAK: { espnAbbr: "oak", name: "Athletics", city: "Oakland" },
  ARI: { espnAbbr: "ari", name: "D-backs", city: "Arizona" },
  ATL: { espnAbbr: "atl", name: "Braves", city: "Atlanta" },
  BAL: { espnAbbr: "bal", name: "Orioles", city: "Baltimore" },
  BOS: { espnAbbr: "bos", name: "Red Sox", city: "Boston" },
  CHA: { espnAbbr: "chw", name: "White Sox", city: "Chicago" },
  CHW: { espnAbbr: "chw", name: "White Sox", city: "Chicago" },
  CHN: { espnAbbr: "chc", name: "Cubs", city: "Chicago" },
  CHC: { espnAbbr: "chc", name: "Cubs", city: "Chicago" },
  CIN: { espnAbbr: "cin", name: "Reds", city: "Cincinnati" },
  CLE: { espnAbbr: "cle", name: "Guardians", city: "Cleveland" },
  COL: { espnAbbr: "col", name: "Rockies", city: "Colorado" },
  DET: { espnAbbr: "det", name: "Tigers", city: "Detroit" },
  HOU: { espnAbbr: "hou", name: "Astros", city: "Houston" },
  KC: { espnAbbr: "kc", name: "Royals", city: "Kansas City" },
  KCA: { espnAbbr: "kc", name: "Royals", city: "Kansas City" },
  LAN: { espnAbbr: "lad", name: "Dodgers", city: "Los Angeles" },
  LAD: { espnAbbr: "lad", name: "Dodgers", city: "Los Angeles" },
  MIA: { espnAbbr: "mia", name: "Marlins", city: "Miami" },
  MIL: { espnAbbr: "mil", name: "Brewers", city: "Milwaukee" },
  MIN: { espnAbbr: "min", name: "Twins", city: "Minnesota" },
  NYA: { espnAbbr: "nyy", name: "Yankees", city: "New York" },
  NYY: { espnAbbr: "nyy", name: "Yankees", city: "New York" },
  NYN: { espnAbbr: "nym", name: "Mets", city: "New York" },
  NYM: { espnAbbr: "nym", name: "Mets", city: "New York" },
  PHI: { espnAbbr: "phi", name: "Phillies", city: "Philadelphia" },
  PIT: { espnAbbr: "pit", name: "Pirates", city: "Pittsburgh" },
  SDN: { espnAbbr: "sd", name: "Padres", city: "San Diego" },
  SD: { espnAbbr: "sd", name: "Padres", city: "San Diego" },
  SFN: { espnAbbr: "sf", name: "Giants", city: "San Francisco" },
  SF: { espnAbbr: "sf", name: "Giants", city: "San Francisco" },
  SEA: { espnAbbr: "sea", name: "Mariners", city: "Seattle" },
  STL: { espnAbbr: "stl", name: "Cardinals", city: "St. Louis" },
  TBA: { espnAbbr: "tb", name: "Rays", city: "Tampa Bay" },
  TB: { espnAbbr: "tb", name: "Rays", city: "Tampa Bay" },
  TEX: { espnAbbr: "tex", name: "Rangers", city: "Texas" },
  TOR: { espnAbbr: "tor", name: "Blue Jays", city: "Toronto" },
  WAS: { espnAbbr: "wsh", name: "Nationals", city: "Washington" },
  WSH: { espnAbbr: "wsh", name: "Nationals", city: "Washington" },
};

/**
 * Get the ESPN CDN logo URL for a team abbreviation.
 */
export function getTeamLogoUrl(abbr: string): string {
  const team = TEAM_MAP[abbr.toUpperCase()];
  if (!team) return "";
  return `https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/${team.espnAbbr}.png`;
}

/**
 * Get team display name from abbreviation.
 */
export function getTeamName(abbr: string): string {
  const team = TEAM_MAP[abbr.toUpperCase()];
  return team ? team.name : abbr;
}

/**
 * Parse a game string like "ANA @ ATH" into away and home teams.
 */
export function parseGameString(game: string): { away: string; home: string } | null {
  const parts = game.split("@").map((s) => s.trim());
  if (parts.length !== 2) return null;
  return { away: parts[0], home: parts[1] };
}
