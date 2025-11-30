"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Bell,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Zap,
  ChevronUp,
  ChevronDown,
  ChevronRight,
  Filter,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  TierBadge,
  Badge,
  Button,
  Select,
  ErrorState,
  LoadingState,
  type Column,
} from "@/components/ui";
import { Header, PageContent, RefreshButton } from "@/components/layout";
import { getRecentAlerts } from "@/lib/api";
import type { AlertResponse, AlertType, AlertSeverity } from "@/lib/types/api";

// Alert type to icon mapping
const getAlertIcon = (type: AlertType) => {
  switch (type) {
    case "NEW_ADS_BOOST":
      return <Zap className="w-4 h-4 text-yellow-400" />;
    case "SCORE_JUMP":
      return <TrendingUp className="w-4 h-4 text-green-400" />;
    case "SCORE_DROP":
      return <TrendingDown className="w-4 h-4 text-red-400" />;
    case "TIER_UP":
      return <ChevronUp className="w-4 h-4 text-green-400" />;
    case "TIER_DOWN":
      return <ChevronDown className="w-4 h-4 text-red-400" />;
    default:
      return <AlertTriangle className="w-4 h-4 text-slate-400" />;
  }
};

// Severity to badge variant mapping
const getSeverityVariant = (severity: AlertSeverity) => {
  switch (severity) {
    case "critical":
      return "error" as const;
    case "warning":
      return "warning" as const;
    case "info":
    default:
      return "info" as const;
  }
};

// Alert type filter options
const ALERT_TYPE_OPTIONS = [
  { value: "", label: "All Types" },
  { value: "NEW_ADS_BOOST", label: "New Ads Boost" },
  { value: "SCORE_JUMP", label: "Score Jump" },
  { value: "SCORE_DROP", label: "Score Drop" },
  { value: "TIER_UP", label: "Tier Up" },
  { value: "TIER_DOWN", label: "Tier Down" },
];

const SEVERITY_OPTIONS = [
  { value: "", label: "All Severities" },
  { value: "critical", label: "Critical" },
  { value: "warning", label: "Warning" },
  { value: "info", label: "Info" },
];

/**
 * Alerts Page
 *
 * Displays a list of all recent alerts across all pages.
 * Allows filtering by type and severity.
 */
export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getRecentAlerts(500);
      setAlerts(response.items);
    } catch (err) {
      console.error("Error fetching alerts:", err);
      setError(err instanceof Error ? err.message : "Failed to load alerts");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter alerts
  const filteredAlerts = alerts.filter((alert) => {
    if (typeFilter && alert.alert_type !== typeFilter) return false;
    if (severityFilter && alert.severity !== severityFilter) return false;
    return true;
  });

  // Group alerts by date
  const groupedAlerts = filteredAlerts.reduce((groups, alert) => {
    const date = new Date(alert.created_at).toLocaleDateString();
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(alert);
    return groups;
  }, {} as Record<string, AlertResponse[]>);

  const hasActiveFilters = typeFilter || severityFilter;

  if (error) {
    return (
      <>
        <Header title="Alerts" subtitle="Recent activity notifications" />
        <PageContent>
          <ErrorState
            title="Failed to load alerts"
            message={error}
            onRetry={fetchData}
          />
        </PageContent>
      </>
    );
  }

  return (
    <>
      <Header
        title="Alerts"
        subtitle={`${alerts.length} recent alerts`}
        actions={<RefreshButton onClick={fetchData} isLoading={isLoading} />}
      />
      <PageContent>
        {/* Filters */}
        <Card className="mb-6">
          <CardBody>
            <div className="flex flex-wrap items-end gap-4">
              <div className="w-48">
                <Select
                  label="Alert Type"
                  options={ALERT_TYPE_OPTIONS}
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                />
              </div>
              <div className="w-40">
                <Select
                  label="Severity"
                  options={SEVERITY_OPTIONS}
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                />
              </div>
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setTypeFilter("");
                    setSeverityFilter("");
                  }}
                  className="flex items-center gap-1"
                >
                  Clear filters
                </Button>
              )}
            </div>
            {hasActiveFilters && (
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-800">
                <Filter className="w-4 h-4 text-slate-500" />
                <span className="text-sm text-slate-500">
                  Showing {filteredAlerts.length} of {alerts.length} alerts
                </span>
              </div>
            )}
          </CardBody>
        </Card>

        {isLoading ? (
          <LoadingState message="Loading alerts..." />
        ) : filteredAlerts.length === 0 ? (
          <Card>
            <CardBody>
              <div className="py-12 text-center">
                <Bell className="w-12 h-12 mx-auto mb-4 text-slate-500 opacity-50" />
                <h3 className="text-lg font-medium text-slate-200 mb-2">
                  {hasActiveFilters ? "No matching alerts" : "No alerts yet"}
                </h3>
                <p className="text-slate-400">
                  {hasActiveFilters
                    ? "Try adjusting your filters"
                    : "Alerts are generated when significant changes occur"}
                </p>
              </div>
            </CardBody>
          </Card>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedAlerts).map(([date, dateAlerts]) => (
              <Card key={date}>
                <CardHeader>
                  <div className="flex items-center gap-2 text-sm">
                    <Bell className="w-4 h-4 text-slate-500" />
                    <span className="font-medium text-slate-300">{date}</span>
                    <Badge variant="default" size="sm">
                      {dateAlerts.length} alert{dateAlerts.length !== 1 ? "s" : ""}
                    </Badge>
                  </div>
                </CardHeader>
                <CardBody className="p-0">
                  <div className="divide-y divide-slate-800">
                    {dateAlerts.map((alert) => (
                      <div
                        key={alert.id}
                        className="flex items-center justify-between p-4 hover:bg-slate-800/30 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
                            {getAlertIcon(alert.alert_type)}
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-medium text-slate-200">
                                {alert.message}
                              </span>
                              <Badge
                                variant={getSeverityVariant(alert.severity)}
                                size="sm"
                              >
                                {alert.severity}
                              </Badge>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-slate-500">
                              <span>
                                {new Date(alert.created_at).toLocaleTimeString()}
                              </span>
                              {alert.old_tier && alert.new_tier && (
                                <span className="flex items-center gap-1">
                                  <TierBadge tier={alert.old_tier as any} size="sm" />
                                  <ChevronRight className="w-3 h-3" />
                                  <TierBadge tier={alert.new_tier as any} size="sm" />
                                </span>
                              )}
                              {alert.old_score !== null && alert.new_score !== null && (
                                <span>
                                  {alert.old_score.toFixed(1)} → {alert.new_score.toFixed(1)}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <Link
                          href={`/pages/${encodeURIComponent(alert.page_id)}`}
                          className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
                        >
                          View Page
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </div>
                    ))}
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </PageContent>
    </>
  );
}
