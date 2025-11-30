"use client";

import clsx from "clsx";
import type { Tier, MatchStrength, Sentiment, QualityTier } from "@/lib/types/api";

interface TierBadgeProps {
  tier: Tier;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface MatchBadgeProps {
  strength: MatchStrength;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface StatusBadgeProps {
  status: "active" | "inactive" | "pending" | "error";
  label?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const tierStyles: Record<Tier, string> = {
  XXL: "bg-green-500/20 text-green-400 border-green-500/30",
  XL: "bg-lime-500/20 text-lime-400 border-lime-500/30",
  L: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  M: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  S: "bg-red-500/20 text-red-400 border-red-500/30",
  XS: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const matchStyles: Record<MatchStrength, string> = {
  strong: "bg-green-500/20 text-green-400 border-green-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  weak: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  none: "bg-gray-500/20 text-gray-400 border-gray-500/30",
};

const statusStyles: Record<string, string> = {
  active: "bg-green-500/20 text-green-400 border-green-500/30",
  inactive: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  error: "bg-red-500/20 text-red-400 border-red-500/30",
};

const sizeStyles = {
  sm: "px-1.5 py-0.5 text-xs",
  md: "px-2 py-0.5 text-xs",
  lg: "px-3 py-1 text-sm",
};

/**
 * Badge component for displaying tier classification.
 * Tiers: XXL (best) -> XS (worst)
 */
export function TierBadge({ tier, size = "md", className }: TierBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border font-semibold uppercase tracking-wide",
        tierStyles[tier],
        sizeStyles[size],
        className
      )}
    >
      {tier}
    </span>
  );
}

/**
 * Badge component for displaying match strength.
 */
export function MatchBadge({
  strength,
  size = "md",
  className,
}: MatchBadgeProps) {
  const labels: Record<MatchStrength, string> = {
    strong: "Strong",
    medium: "Medium",
    weak: "Weak",
    none: "None",
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border font-medium capitalize",
        matchStyles[strength],
        sizeStyles[size],
        className
      )}
    >
      {labels[strength]}
    </span>
  );
}

/**
 * Badge component for displaying status.
 */
export function StatusBadge({
  status,
  label,
  size = "md",
  className,
}: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border font-medium capitalize",
        statusStyles[status],
        sizeStyles[size],
        className
      )}
    >
      {label || status}
    </span>
  );
}

/**
 * Generic badge component.
 */
export function Badge({
  children,
  variant = "default",
  size = "md",
  className,
}: {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const variantStyles = {
    default: "bg-slate-700/50 text-slate-300 border-slate-600/50",
    success: "bg-green-500/20 text-green-400 border-green-500/30",
    warning: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    error: "bg-red-500/20 text-red-400 border-red-500/30",
    info: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border font-medium",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
    >
      {children}
    </span>
  );
}

// =============================================================================
// Creative Analysis Badges (Sprint 9)
// =============================================================================

interface SentimentBadgeProps {
  sentiment: Sentiment;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface QualityBadgeProps {
  tier: QualityTier;
  size?: "sm" | "md" | "lg";
  className?: string;
}

interface CreativeScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sentimentStyles: Record<Sentiment, string> = {
  positive: "bg-green-500/20 text-green-400 border-green-500/30",
  neutral: "bg-gray-500/20 text-gray-400 border-gray-500/30",
  negative: "bg-red-500/20 text-red-400 border-red-500/30",
};

const sentimentIcons: Record<Sentiment, string> = {
  positive: "😊",
  neutral: "😐",
  negative: "😟",
};

const qualityStyles: Record<QualityTier, string> = {
  excellent: "bg-green-500/20 text-green-400 border-green-500/30",
  good: "bg-lime-500/20 text-lime-400 border-lime-500/30",
  average: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  poor: "bg-red-500/20 text-red-400 border-red-500/30",
};

/**
 * Badge component for displaying sentiment.
 */
export function SentimentBadge({
  sentiment,
  size = "md",
  className,
}: SentimentBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full border font-medium capitalize",
        sentimentStyles[sentiment],
        sizeStyles[size],
        className
      )}
    >
      <span>{sentimentIcons[sentiment]}</span>
      <span>{sentiment}</span>
    </span>
  );
}

/**
 * Badge component for displaying quality tier.
 */
export function QualityBadge({
  tier,
  size = "md",
  className,
}: QualityBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border font-medium capitalize",
        qualityStyles[tier],
        sizeStyles[size],
        className
      )}
    >
      {tier}
    </span>
  );
}

/**
 * Badge component for displaying creative score.
 * Score is color-coded: 70+ green, 50-70 yellow, <50 red.
 */
export function CreativeScoreBadge({
  score,
  size = "md",
  className,
}: CreativeScoreBadgeProps) {
  const getScoreStyle = (s: number): string => {
    if (s >= 70) return "bg-green-500/20 text-green-400 border-green-500/30";
    if (s >= 50) return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    return "bg-red-500/20 text-red-400 border-red-500/30";
  };

  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full border font-bold tabular-nums",
        getScoreStyle(score),
        sizeStyles[size],
        className
      )}
    >
      {score.toFixed(0)}
    </span>
  );
}
