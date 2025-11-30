"use client";

import clsx from "clsx";
import { ReactNode } from "react";

interface KpiTileProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  subtitle?: string;
  className?: string;
  isLoading?: boolean;
}

/**
 * KPI Tile component for displaying key metrics.
 * Shows a large value with a label and optional trend indicator.
 */
export function KpiTile({
  label,
  value,
  icon,
  trend,
  subtitle,
  className,
  isLoading = false,
}: KpiTileProps) {
  if (isLoading) {
    return (
      <div
        className={clsx(
          "bg-slate-900 rounded-lg border border-slate-800 p-6",
          className
        )}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 w-24 bg-slate-700 rounded animate-pulse" />
          {icon && (
            <div className="h-8 w-8 bg-slate-700 rounded animate-pulse" />
          )}
        </div>
        <div className="h-8 w-20 bg-slate-700 rounded animate-pulse mb-2" />
        <div className="h-3 w-16 bg-slate-700 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div
      className={clsx(
        "bg-slate-900 rounded-lg border border-slate-800 p-6",
        className
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-slate-400">{label}</span>
        {icon && <div className="text-slate-500">{icon}</div>}
      </div>

      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-bold text-slate-100">{value}</span>
        {trend && (
          <span
            className={clsx(
              "text-sm font-medium flex items-center",
              trend.isPositive ? "text-green-400" : "text-red-400"
            )}
          >
            <svg
              className={clsx(
                "w-4 h-4 mr-0.5",
                !trend.isPositive && "rotate-180"
              )}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 15l7-7 7 7"
              />
            </svg>
            {Math.abs(trend.value)}%
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
      )}
    </div>
  );
}

/**
 * KPI Grid component for arranging multiple KPI tiles.
 */
export function KpiGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4",
        className
      )}
    >
      {children}
    </div>
  );
}
