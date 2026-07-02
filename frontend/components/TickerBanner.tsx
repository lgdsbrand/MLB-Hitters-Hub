"use client";

import { useMemo } from "react";
import { getTeamLogoUrl, parseGameString } from "@/lib/teamLogos";

interface TickerItem {
  awayTeam: string;
  homeTeam: string;
  awayLogo: string;
  homeLogo: string;
  gameLabel: string;
  ou?: string;
  pred?: string;
  odds?: string;
  pitcher?: string;
}

interface TickerBannerProps {
  games?: string[];
  hitsData?: Record<string, unknown>[];
  hrData?: Record<string, unknown>[];
  tbData?: Record<string, unknown>[];
  loading?: boolean;
}

export default function TickerBanner({
  games = [],
  hitsData = [],
  hrData = [],
  tbData = [],
  loading = false,
}: TickerBannerProps) {
  // Build ticker items from available data
  const tickerItems: TickerItem[] = useMemo(() => {
    const items: TickerItem[] = [];
    const seen = new Set<string>();

    // Helper to add an item
    const addItem = (
      gameStr: string,
      ou?: string,
      pred?: string,
      odds?: string,
      pitcher?: string,
    ) => {
      if (seen.has(gameStr)) return;
      seen.add(gameStr);

      const parsed = parseGameString(gameStr);
      if (!parsed) return;

      items.push({
        awayTeam: parsed.away,
        homeTeam: parsed.home,
        awayLogo: getTeamLogoUrl(parsed.away),
        homeLogo: getTeamLogoUrl(parsed.home),
        gameLabel: gameStr,
        ou,
        pred,
        odds,
        pitcher,
      });
    };

    // Add from hits data (has O/U and Odds)
    hitsData.forEach((row) => {
      const game = String(row["Game"] || row["game"] || "");
      if (!game) return;
      const ou = String(row["O/U"] || row["OU"] || "");
      const pred = row["Pred"] ? `${row["Pred"]}` : "";
      const odds = String(row["Odds"] || "");
      const pitcher = String(row["Pitcher"] || "");
      addItem(game, ou, pred, odds, pitcher);
    });

    // Add from TB data (has Line and Over)
    tbData.forEach((row) => {
      const game = String(row["Game"] || row["game"] || "");
      if (!game) return;
      const line = String(row["Line"] || "");
      const overOdds = String(row["Over"] || "");
      const pred = row["TB Pred"] ? `${row["TB Pred"]}` : "";
      const pitcher = String(row["Pitcher"] || "");
      addItem(game, `O/U ${line} (${overOdds})`, pred, "", pitcher);
    });

    // Add from HR data if no hits/tb data for that game
    hrData.forEach((row) => {
      const game = String(row["Game"] || row["game"] || "");
      if (seen.has(game)) return;
      const odds = String(row["Odds"] || "");
      const pred = row["HR Pred"] ? `${row["HR Pred"]}` : "";
      const pitcher = String(row["Pitcher"] || "");
      addItem(game, "", pred, odds, pitcher);
    });

    // If no data at all, show games list
    if (items.length === 0) {
      games.forEach((game) => {
        const parsed = parseGameString(game);
        if (!parsed || seen.has(game)) return;
        seen.add(game);
        items.push({
          awayTeam: parsed.away,
          homeTeam: parsed.home,
          awayLogo: getTeamLogoUrl(parsed.away),
          homeLogo: getTeamLogoUrl(parsed.home),
          gameLabel: game,
        });
      });
    }

    return items;
  }, [games, hitsData, hrData, tbData]);

  // Duplicate items for seamless scrolling
  const duplicatedItems = useMemo(
    () => [...tickerItems, ...tickerItems, ...tickerItems],
    [tickerItems],
  );

  if (loading && tickerItems.length === 0) {
    return (
      <div className="ticker-banner">
        <div className="ticker-inner">
          <span className="text-text-muted text-xs">
            Loading game data...
          </span>
        </div>
      </div>
    );
  }

  if (tickerItems.length === 0) return null;

  return (
    <div className="ticker-banner">
      <div className="ticker-inner">
        <div className="ticker-track">
          {duplicatedItems.map((item, idx) => (
            <div key={`${item.gameLabel}-${idx}`} className="ticker-item">
              {/* Away Logo - only render if URL exists */}
              {item.awayLogo && (
                <img
                  src={item.awayLogo}
                  alt={item.awayTeam}
                  className="ticker-logo"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              )}
                <span className="ticker-vs">vs</span>
              {/* Home Logo - only render if URL exists */}
              {item.homeLogo && (
                <img
                  src={item.homeLogo}
                  alt={item.homeTeam}
                  className="ticker-logo"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              )}

              {/* Game info block */}
              <div className="ticker-info">
                <span className="ticker-teams">
                  {item.awayTeam} vs {item.homeTeam}
                </span>
                {item.pitcher && (
                  <span className="ticker-pitcher">vs {item.pitcher}</span>
                )}
                {item.ou && <span className="ticker-ou">O/U: {item.ou}</span>}
                {item.pred && (
                  <span className="ticker-pred">Pred: {item.pred}</span>
                )}
                {item.odds && !item.pred && (
                  <span className="ticker-odds">Odds: {item.odds}</span>
                )}
              </div>

              {/* Separator */}
              <div className="ticker-separator">
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}