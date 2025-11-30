"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Activity,
  Database,
  Bell,
  Calendar,
  Server,
  Store,
  Search,
  Clock,
  ChevronRight,
  Play,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  Table,
  KpiTile,
  Badge,
  Button,
  ErrorState,
  LoadingState,
  type Column,
} from "@/components/ui";
import { Header, PageContent, RefreshButton } from "@/components/layout";
import {
  getMonitoringSummary,
  getAdminKeywords,
  getAdminScans,
  triggerDailySnapshot,
} from "@/lib/api";
import type {
  MonitoringSummary,
  AdminKeywordRunResponse,
  AdminScanResponse,
} from "@/lib/types/api";

/**
 * Monitoring Page
 *
 * System status dashboard showing:
 * - Summary statistics (pages, scores, alerts)
 * - Recent keyword runs
 * - Recent scans
 * - Admin actions (trigger snapshot)
 */
export default function MonitoringPage() {
  const [summary, setSummary] = useState<MonitoringSummary | null>(null);
  const [keywords, setKeywords] = useState<AdminKeywordRunResponse[]>([]);
  const [scans, setScans] = useState<AdminScanResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [triggerMessage, setTriggerMessage] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [summaryData, keywordsData, scansData] = await Promise.allSettled([
        getMonitoringSummary(),
        getAdminKeywords(20),
        getAdminScans({ limit: 20 }),
      ]);

      if (summaryData.status === "fulfilled") {
        setSummary(summaryData.value);
      }
      if (keywordsData.status === "fulfilled") {
        setKeywords(keywordsData.value.items);
      }
      if (scansData.status === "fulfilled") {
        setScans(scansData.value.items);
      }
    } catch (err) {
      console.error("Error fetching monitoring data:", err);
      setError(err instanceof Error ? err.message : "Failed to load monitoring data");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTriggerSnapshot = async () => {
    setIsTriggering(true);
    setTriggerMessage(null);
    try {
      const result = await triggerDailySnapshot();
      setTriggerMessage(`Snapshot triggered: Task ID ${result.task_id}`);
    } catch (err) {
      console.error("Error triggering snapshot:", err);
      setTriggerMessage("Failed to trigger snapshot");
    } finally {
      setIsTriggering(false);
    }
  };

  // Keyword runs table columns
  const keywordColumns: Column<AdminKeywordRunResponse>[] = [
    {
      key: "keyword",
      header: "Keyword",
      render: (item) => (
        <span className="font-medium text-slate-200">{item.keyword}</span>
      ),
    },
    {
      key: "country",
      header: "Country",
      render: (item) => (
        <Badge variant="default" size="sm">
          {item.country}
        </Badge>
      ),
      className: "w-24",
    },
    {
      key: "ads_found",
      header: "Ads",
      render: (item) => (
        <span className="text-slate-300">{item.total_ads_found}</span>
      ),
      className: "w-20 text-right",
    },
    {
      key: "pages_found",
      header: "Pages",
      render: (item) => (
        <span className="text-slate-300">{item.total_pages_found}</span>
      ),
      className: "w-20 text-right",
    },
    {
      key: "created_at",
      header: "Run Date",
      render: (item) => (
        <span className="text-sm text-slate-400">
          {new Date(item.created_at).toLocaleString()}
        </span>
      ),
      className: "w-40",
    },
  ];

  // Scans table columns
  const scanColumns: Column<AdminScanResponse>[] = [
    {
      key: "id",
      header: "Scan ID",
      render: (item) => (
        <span className="font-mono text-xs text-slate-400">
          {item.id.slice(0, 8)}...
        </span>
      ),
      className: "w-28",
    },
    {
      key: "status",
      header: "Status",
      render: (item) => {
        const variant =
          item.status === "completed"
            ? "success"
            : item.status === "failed"
            ? "error"
            : item.status === "running"
            ? "warning"
            : "default";
        return (
          <Badge variant={variant as any} size="sm">
            {item.status}
          </Badge>
        );
      },
      className: "w-24",
    },
    {
      key: "result",
      header: "Result",
      render: (item) => (
        <span className="text-sm text-slate-400">
          {item.result_summary || "-"}
        </span>
      ),
    },
    {
      key: "started_at",
      header: "Started",
      render: (item) => (
        <span className="text-sm text-slate-400">
          {item.started_at
            ? new Date(item.started_at).toLocaleTimeString()
            : "-"}
        </span>
      ),
      className: "w-28",
    },
  ];

  if (error) {
    return (
      <>
        <Header title="Monitoring" subtitle="System status dashboard" />
        <PageContent>
          <ErrorState
            title="Failed to load monitoring data"
            message={error}
            onRetry={fetchData}
          />
        </PageContent>
      </>
    );
  }

  if (isLoading) {
    return (
      <>
        <Header title="Monitoring" subtitle="System status dashboard" />
        <PageContent>
          <LoadingState message="Loading monitoring data..." />
        </PageContent>
      </>
    );
  }

  return (
    <>
      <Header
        title="Monitoring"
        subtitle="System status dashboard"
        actions={<RefreshButton onClick={fetchData} isLoading={isLoading} />}
      />
      <PageContent>
        {/* Summary Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KpiTile
            label="Total Pages"
            value={summary?.total_pages ?? 0}
            icon={<Store className="w-5 h-5" />}
          />
          <KpiTile
            label="Pages with Scores"
            value={summary?.pages_with_scores ?? 0}
            icon={<Database className="w-5 h-5" />}
          />
          <KpiTile
            label="Alerts (24h)"
            value={summary?.alerts_last_24h ?? 0}
            icon={<Bell className="w-5 h-5" />}
          />
          <KpiTile
            label="Alerts (7d)"
            value={summary?.alerts_last_7d ?? 0}
            icon={<Bell className="w-5 h-5" />}
          />
        </div>

        {/* System Info */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-green-400" />
                System Status
              </div>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div className="flex items-center justify-between py-2 border-b border-slate-800">
                  <span className="text-slate-400">Last Metrics Snapshot</span>
                  <span className="text-slate-200">
                    {summary?.last_metrics_snapshot_date || "Never"}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-800">
                  <span className="text-slate-400">Metrics Snapshots</span>
                  <span className="text-slate-200">
                    {summary?.metrics_snapshots_count ?? 0} entries
                  </span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-800">
                  <span className="text-slate-400">Summary Generated</span>
                  <span className="text-slate-200">
                    {summary?.generated_at
                      ? new Date(summary.generated_at).toLocaleString()
                      : "-"}
                  </span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-slate-400">Score Coverage</span>
                  <span className="text-slate-200">
                    {summary && summary.total_pages > 0
                      ? `${((summary.pages_with_scores / summary.total_pages) * 100).toFixed(1)}%`
                      : "N/A"}
                  </span>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Admin Actions */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-blue-400" />
                Admin Actions
              </div>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2">
                    Daily Metrics Snapshot
                  </h4>
                  <p className="text-sm text-slate-500 mb-3">
                    Trigger a manual snapshot of daily metrics for all pages.
                  </p>
                  <Button
                    variant="secondary"
                    onClick={handleTriggerSnapshot}
                    disabled={isTriggering}
                    className="flex items-center gap-2"
                  >
                    <Play className={`w-4 h-4 ${isTriggering ? "animate-pulse" : ""}`} />
                    {isTriggering ? "Triggering..." : "Trigger Snapshot"}
                  </Button>
                  {triggerMessage && (
                    <p className="text-sm text-blue-400 mt-2">{triggerMessage}</p>
                  )}
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Recent Keywords */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Search className="w-5 h-5 text-purple-400" />
              Recent Keyword Runs
            </div>
          </CardHeader>
          <CardBody className="p-0">
            {keywords.length === 0 ? (
              <div className="py-8 text-center text-slate-500">
                No keyword runs recorded yet
              </div>
            ) : (
              <Table
                columns={keywordColumns}
                data={keywords}
                keyExtractor={(item) => item.scan_id}
                emptyMessage="No keyword runs"
              />
            )}
          </CardBody>
        </Card>

        {/* Recent Scans */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-orange-400" />
              Recent Scans
            </div>
          </CardHeader>
          <CardBody className="p-0">
            {scans.length === 0 ? (
              <div className="py-8 text-center text-slate-500">
                No scans recorded yet
              </div>
            ) : (
              <Table
                columns={scanColumns}
                data={scans}
                keyExtractor={(item) => item.id}
                emptyMessage="No scans"
              />
            )}
          </CardBody>
        </Card>
      </PageContent>
    </>
  );
}
