"use client";

import DataTable from "./DataTable";
import { HitStreak } from "@/lib/api";

interface HitStreaksTableProps {
  data: HitStreak[];
  loading?: boolean;
}

export default function HitStreaksTable({ data, loading = false }: HitStreaksTableProps) {
  const columns = [
    { key: "Player", label: "Player" },
    { key: "Team", label: "Team" },
    { key: "Streak", label: "Streak", align: "center" as const },
    { key: "Games", label: "Games", align: "center" as const },
    { key: "AVG", label: "AVG", align: "center" as const },
    { key: "Hits", label: "Hits", align: "center" as const },
    { key: "HR", label: "HR", align: "center" as const },
    { key: "RBI", label: "RBI", align: "center" as const },
    { key: "Runs", label: "Runs", align: "center" as const },
    { key: "OPS", label: "OPS", align: "center" as const },
  ];

  return (
    <div className="mt-8 mb-8">
      <h2 className="text-xl font-bold text-text-primary mb-4 flex items-center gap-2">
        <span className="text-accent-gold">📊</span>
        Active Hit Streaks
      </h2>
      <DataTable
        columns={columns}
        data={data}
        onAdd={() => {}}
        isSelected={() => false}
        source="hit-streaks"
        loading={loading}
        emptyMessage="No active hit streaks available."
        batterKey="Player"
        gameKey="Team"
      />
    </div>
  );
}
