"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Store,
  TrendingUp,
  Activity,
  Calendar,
  ExternalLink,
  ChevronRight,
  Bell,
  Eye,
  AlertTriangle,
  Zap,
  TrendingDown,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  KpiTile,
  KpiGrid,
  Table,
  TierBadge,
  Button,
  ErrorState,
  type Column,
} from "@/components/ui";
import { Header, PageContent, RefreshButton } from "@/components/layout";
import { getTopPages, getRankedPages, listPages, getRecentAlerts, getWatchlists } from "@/lib/api";
import type { TopShopEntry, AlertResponse, WatchlistSummary } from "@/lib/types/api";

interface DashboardStats {
  totalPages: number;
  shopifyPages: number;
  tierXXLCount: number;
  tierXLCount: number;
  lastSnapshotDate: string | null;
}

/**
 * Main Dashboard Page
 *
 * Displays key metrics and top-ranked pages/shops.
 */
export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [topPages, setTopPages] = useState<TopShopEntry[]>([]);
  const [recentAlerts, setRecentAlerts] = useState<AlertResponse[]>([]);
  const [watchlists, setWatchlists] = useState<WatchlistSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get alert icon based on type
  const getAlertIcon = (type: string) => {
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

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch data in parallel
      const [topPagesResponse, allPagesResponse, xxlTierResponse, xlTierResponse, alertsResponse, watchlistsResponse] =
        await Promise.allSettled([
          getTopPages(20, 0),
          listPages({ page_size: 1 }), // Get total count
          getRankedPages({ tier: "XXL", limit: 1 }), // Get XXL tier count
          getRankedPages({ tier: "XL", limit: 1 }), // Get XL tier count
          getRecentAlerts(5),
          getWatchlists(5),
        ]);

      if (topPagesResponse.status === "fulfilled") {
        setTopPages(topPagesResponse.value.items);
      }

      if (alertsResponse.status === "fulfilled") {
        setRecentAlerts(alertsResponse.value.items);
      }

      if (watchlistsResponse.status === "fulfilled") {
        setWatchlists(watchlistsResponse.value.items);
      }

      setStats({
        totalPages: allPagesResponse.status === "fulfilled" ? allPagesResponse.value.total : 0,
        // TODO: Backend should expose shopify count directly
        shopifyPages: 0,
        tierXXLCount: xxlTierResponse.status === "fulfilled" ? xxlTierResponse.value.total : 0,
        tierXLCount: xlTierResponse.status === "fulfilled" ? xlTierResponse.value.total : 0,
        // TODO: Backend should expose last snapshot date
        lastSnapshotDate: null,
      });
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError(
        err instanceof Error ? err.message : "Failed to load dashboard data"
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Table columns for top pages
  const columns: Column<TopShopEntry>[] = [
    {
      key: "rank",
      header: "#",
      render: (item) => (
        <span className="text-slate-500 font-mono">{item.rank}</span>
      ),
      className: "w-12",
    },
    {
      key: "domain",
      header: "Page / Domain",
      render: (item) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
            <Store className="w-4 h-4 text-slate-500" />
          </div>
          <div>
            <p className="font-medium text-slate-200">{item.domain}</p>
            <p className="text-xs text-slate-500 truncate max-w-[200px]">
              {item.page_id}
            </p>
          </div>
        </div>
      ),
    },
    {
      key: "score",
      header: "Score",
      render: (item) => (
        <span className="font-semibold text-slate-200">
          {item.score.toFixed(1)}
        </span>
      ),
      className: "text-right",
    },
    {
      key: "tier",
      header: "Tier",
      render: (item) => <TierBadge tier={item.tier} />,
    },
    {
      key: "actions",
      header: "",
      render: (item) => (
        <Link
          href={`/pages/${encodeURIComponent(item.page_id)}`}
          className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
        >
          View
          <ChevronRight className="w-4 h-4" />
        </Link>
      ),
      className: "w-20",
    },
  ];

  if (error) {
    return (
      <>
        <Header title="Dashboard" subtitle="Market Intelligence Overview" />
        <PageContent>
          <ErrorState
            title="Failed to load dashboard"
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
        title="Dashboard"
        subtitle="Market Intelligence Overview"
        actions={
          <RefreshButton onClick={fetchData} isLoading={isLoading} />
        }
      />
      <PageContent>
        {/* KPI Section */}
        <KpiGrid className="mb-8">
          <KpiTile
            label="Total Pages Tracked"
            value={stats?.totalPages ?? "-"}
            icon={<Store className="w-5 h-5" />}
            isLoading={isLoading}
          />
          <KpiTile
            label="Tier XXL (Top)"
            value={stats?.tierXXLCount ?? "-"}
            icon={<TrendingUp className="w-5 h-5" />}
            subtitle="Score 85-100"
            isLoading={isLoading}
          />
          <KpiTile
            label="Tier XL"
            value={stats?.tierXLCount ?? "-"}
            icon={<Activity className="w-5 h-5" />}
            subtitle="Score 70-85"
            isLoading={isLoading}
          />
          <KpiTile
            label="Last Snapshot"
            value={stats?.lastSnapshotDate ?? "N/A"}
            icon={<Calendar className="w-5 h-5" />}
            subtitle="TODO: Add backend endpoint"
            isLoading={isLoading}
          />
        </KpiGrid>

        {/* Top Pages Table */}
        <Card>
          <CardHeader
            action={
              <Link
                href="/pages"
                className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
              >
                View all pages
                <ExternalLink className="w-4 h-4" />
              </Link>
            }
          >
            Top 20 Pages
          </CardHeader>
          <CardBody className="p-0">
            <Table
              columns={columns}
              data={topPages}
              keyExtractor={(item) => item.page_id}
              isLoading={isLoading}
              emptyMessage="No pages found. Start tracking some pages!"
            />
          </CardBody>
        </Card>

        {/* Alerts & Watchlists Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
          {/* Recent Alerts */}
          <Card>
            <CardHeader
              action={
                <Link
                  href="/alerts"
                  className="text-sm text-blue-400 hover:text-blue-300"
                >
                  View all
                </Link>
              }
            >
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-orange-400" />
                Recent Alerts
              </div>
            </CardHeader>
            <CardBody>
              {recentAlerts.length > 0 ? (
                <div className="space-y-2">
                  {recentAlerts.map((alert) => (
                    <Link
                      key={alert.id}
                      href={`/pages/${encodeURIComponent(alert.page_id)}`}
                      className="flex items-start gap-3 p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
                    >
                      <div className="mt-0.5">{getAlertIcon(alert.alert_type)}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-200 line-clamp-1">
                          {alert.message}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {new Date(alert.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-slate-500">
                  <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No recent alerts</p>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Watchlists */}
          <Card>
            <CardHeader
              action={
                <Link
                  href="/watchlists"
                  className="text-sm text-blue-400 hover:text-blue-300"
                >
                  View all
                </Link>
              }
            >
              <div className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-blue-400" />
                Your Watchlists
              </div>
            </CardHeader>
            <CardBody>
              {watchlists.length > 0 ? (
                <div className="space-y-2">
                  {watchlists.map((watchlist) => (
                    <Link
                      key={watchlist.id}
                      href={`/watchlists/${encodeURIComponent(watchlist.id)}`}
                      className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <Eye className="w-4 h-4 text-blue-400" />
                        <div>
                          <p className="text-sm text-slate-200">{watchlist.name}</p>
                          <p className="text-xs text-slate-500">{watchlist.pages_count} pages</p>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-500" />
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-slate-500">
                  <Eye className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No watchlists created yet</p>
                  <Link
                    href="/watchlists"
                    className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block"
                  >
                    Create your first watchlist
                  </Link>
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
          <Card>
            <CardBody>
              <h3 className="font-semibold text-slate-200 mb-2">
                Quick Actions
              </h3>
              <div className="space-y-2">
                <Link
                  href="/pages"
                  className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <Store className="w-4 h-4" />
                  <span>Browse all pages</span>
                </Link>
                <Link
                  href="/watchlists"
                  className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <Eye className="w-4 h-4" />
                  <span>Manage watchlists</span>
                </Link>
                <Link
                  href="/monitoring"
                  className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <Activity className="w-4 h-4" />
                  <span>System monitoring</span>
                </Link>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardBody>
              <h3 className="font-semibold text-slate-200 mb-2">
                About Tiers
              </h3>
              <div className="space-y-1 text-sm">
                <div className="flex items-center gap-2">
                  <TierBadge tier="XXL" size="sm" />
                  <span className="text-slate-400">85-100 - Top performers</span>
                </div>
                <div className="flex items-center gap-2">
                  <TierBadge tier="XL" size="sm" />
                  <span className="text-slate-400">70-85 - High potential</span>
                </div>
                <div className="flex items-center gap-2">
                  <TierBadge tier="L" size="sm" />
                  <span className="text-slate-400">55-70 - Good</span>
                </div>
                <div className="flex items-center gap-2">
                  <TierBadge tier="M" size="sm" />
                  <span className="text-slate-400">40-55 - Average</span>
                </div>
                <div className="flex items-center gap-2">
                  <TierBadge tier="S" size="sm" />
                  <span className="text-slate-400">25-40 - Below average</span>
                </div>
                <div className="flex items-center gap-2">
                  <TierBadge tier="XS" size="sm" />
                  <span className="text-slate-400">0-25 - Low activity</span>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>
      </PageContent>
    </>
  );
}
