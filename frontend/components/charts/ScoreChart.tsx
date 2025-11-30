"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { PageDailyMetrics } from "@/lib/types/api";

interface ScoreChartProps {
  data: PageDailyMetrics[];
  height?: number;
  showAdsCount?: boolean;
}

/**
 * Score evolution chart component.
 * Displays shop_score over time with optional ads_count.
 */
export function ScoreChart({
  data,
  height = 300,
  showAdsCount = true,
}: ScoreChartProps) {
  // Format data for Recharts
  const chartData = data.map((m) => ({
    date: new Date(m.date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    fullDate: m.date,
    score: m.shop_score,
    ads: m.ads_count,
    tier: m.tier,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-lg">
          <p className="text-sm text-slate-400 mb-1">{data.fullDate}</p>
          <p className="text-sm font-medium text-blue-400">
            Score: {data.score.toFixed(1)}
          </p>
          {showAdsCount && (
            <p className="text-sm font-medium text-green-400">
              Ads: {data.ads}
            </p>
          )}
          <p className="text-xs text-slate-500 mt-1">Tier: {data.tier}</p>
        </div>
      );
    }
    return null;
  };

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-slate-500"
        style={{ height }}
      >
        No metrics data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={chartData}
        margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="date"
          stroke="#64748b"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          yAxisId="left"
          stroke="#64748b"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          domain={[0, 100]}
        />
        {showAdsCount && (
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
        )}
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ paddingTop: 10 }}
          formatter={(value) => (
            <span className="text-slate-400 text-sm">{value}</span>
          )}
        />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="score"
          name="Shop Score"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, stroke: "#3b82f6", strokeWidth: 2 }}
        />
        {showAdsCount && (
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="ads"
            name="Ads Count"
            stroke="#22c55e"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: "#22c55e", strokeWidth: 2 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}

/**
 * Mini sparkline chart for compact display.
 */
export function MiniScoreChart({
  data,
  height = 40,
  color = "#3b82f6",
}: {
  data: PageDailyMetrics[];
  height?: number;
  color?: string;
}) {
  const chartData = data.map((m) => ({
    score: m.shop_score,
  }));

  if (data.length === 0) {
    return <div className="w-full" style={{ height }} />;
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="score"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
