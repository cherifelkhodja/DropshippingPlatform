"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Eye,
  Store,
  Globe,
  TrendingUp,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Trash2,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  Table,
  TierBadge,
  Badge,
  Button,
  ErrorState,
  LoadingState,
  KpiTile,
  type Column,
} from "@/components/ui";
import { Header, PageContent, Breadcrumbs, RefreshButton } from "@/components/layout";
import {
  getWatchlistWithDetails,
  rescoreWatchlist,
  removePageFromWatchlist,
} from "@/lib/api";
import type { WatchlistWithDetails, WatchlistPageInfo } from "@/lib/types/api";

/**
 * Watchlist Detail Page
 *
 * Shows a single watchlist with all its pages and their scores.
 * Allows triggering a rescore for all pages in the watchlist.
 */
export default function WatchlistDetailPage() {
  const params = useParams();
  const watchlistId = decodeURIComponent(params.id as string);

  const [watchlist, setWatchlist] = useState<WatchlistWithDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRescoring, setIsRescoring] = useState(false);
  const [rescoreMessage, setRescoreMessage] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getWatchlistWithDetails(watchlistId);
      setWatchlist(data);
    } catch (err) {
      console.error("Error fetching watchlist:", err);
      setError(err instanceof Error ? err.message : "Failed to load watchlist");
    } finally {
      setIsLoading(false);
    }
  }, [watchlistId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRescore = async () => {
    setIsRescoring(true);
    setRescoreMessage(null);
    try {
      const result = await rescoreWatchlist(watchlistId);
      setRescoreMessage(result.message);
    } catch (err) {
      console.error("Error rescoring watchlist:", err);
      setRescoreMessage("Failed to trigger rescore");
    } finally {
      setIsRescoring(false);
    }
  };

  const handleRemovePage = async (pageId: string) => {
    if (!confirm("Remove this page from the watchlist?")) return;

    try {
      await removePageFromWatchlist(watchlistId, pageId);
      await fetchData();
    } catch (err) {
      console.error("Error removing page:", err);
    }
  };

  // Calculate stats
  const avgScore = watchlist?.pages.length
    ? watchlist.pages.reduce((sum, p) => sum + p.shop_score, 0) / watchlist.pages.length
    : 0;
  const shopifyCount = watchlist?.pages.filter((p) => p.is_shopify).length || 0;
  const totalAds = watchlist?.pages.reduce((sum, p) => sum + p.active_ads_count, 0) || 0;

  // Table columns
  const columns: Column<WatchlistPageInfo>[] = [
    {
      key: "page",
      header: "Page / Shop",
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">
            <Store className="w-5 h-5 text-slate-500" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-slate-200">
              {item.page_name}
            </p>
            <p className="text-xs text-slate-500 truncate max-w-[250px]">
              {item.url}
            </p>
          </div>
        </div>
      ),
    },
    {
      key: "country",
      header: "Country",
      render: (item) => (
        <div className="flex items-center gap-1">
          {item.country && <Globe className="w-3 h-3 text-slate-500" />}
          <span className="text-slate-300">
            {item.country || "-"}
          </span>
        </div>
      ),
      className: "w-24",
    },
    {
      key: "shopify",
      header: "Type",
      render: (item) => (
        item.is_shopify ? (
          <Badge variant="success" size="sm">Shopify</Badge>
        ) : (
          <Badge variant="default" size="sm">Other</Badge>
        )
      ),
      className: "w-24",
    },
    {
      key: "score",
      header: "Score",
      render: (item) => (
        <span className="font-semibold text-slate-200">
          {item.shop_score.toFixed(1)}
        </span>
      ),
      className: "w-24 text-right",
    },
    {
      key: "tier",
      header: "Tier",
      render: (item) => <TierBadge tier={item.tier} />,
      className: "w-24",
    },
    {
      key: "ads",
      header: "Ads",
      render: (item) => (
        <div className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3 text-blue-400" />
          <span className="text-slate-300">{item.active_ads_count}</span>
        </div>
      ),
      className: "w-20",
    },
    {
      key: "actions",
      header: "",
      render: (item) => (
        <div className="flex items-center gap-2">
          <Link
            href={`/pages/${encodeURIComponent(item.page_id)}`}
            className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
          >
            View
            <ChevronRight className="w-4 h-4" />
          </Link>
          <button
            onClick={() => handleRemovePage(item.page_id)}
            className="p-1 text-slate-500 hover:text-red-400 transition-colors"
            title="Remove from watchlist"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
      className: "w-32",
    },
  ];

  if (isLoading) {
    return (
      <>
        <Header title="Watchlist" subtitle="Loading..." />
        <PageContent>
          <LoadingState message="Loading watchlist..." />
        </PageContent>
      </>
    );
  }

  if (error || !watchlist) {
    return (
      <>
        <Header title="Watchlist" />
        <PageContent>
          <ErrorState
            title="Watchlist not found"
            message={error || "The requested watchlist could not be found"}
            onRetry={fetchData}
          />
        </PageContent>
      </>
    );
  }

  return (
    <>
      <Header
        title={watchlist.name}
        subtitle={watchlist.description || `${watchlist.pages_count} pages tracked`}
        actions={
          <div className="flex items-center gap-2">
            <RefreshButton onClick={fetchData} isLoading={isLoading} />
            <Button
              variant="secondary"
              onClick={handleRescore}
              disabled={isRescoring || watchlist.pages_count === 0}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isRescoring ? "animate-spin" : ""}`} />
              {isRescoring ? "Rescoring..." : "Rescore All"}
            </Button>
          </div>
        }
      />
      <PageContent>
        {/* Breadcrumbs */}
        <div className="mb-6">
          <Breadcrumbs
            items={[
              { label: "Watchlists", href: "/watchlists" },
              { label: watchlist.name },
            ]}
          />
        </div>

        {/* Rescore message */}
        {rescoreMessage && (
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg text-blue-300 text-sm">
            {rescoreMessage}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KpiTile
            label="Pages"
            value={watchlist.pages_count}
            icon={<Store className="w-5 h-5" />}
          />
          <KpiTile
            label="Avg Score"
            value={avgScore.toFixed(1)}
            icon={<TrendingUp className="w-5 h-5" />}
          />
          <KpiTile
            label="Shopify Stores"
            value={shopifyCount}
            icon={<Eye className="w-5 h-5" />}
          />
          <KpiTile
            label="Total Active Ads"
            value={totalAds}
            icon={<TrendingUp className="w-5 h-5" />}
          />
        </div>

        {/* Pages Table */}
        <Card>
          <CardHeader
            action={
              <Badge variant="info" size="sm">
                {watchlist.is_active ? "Active" : "Inactive"}
              </Badge>
            }
          >
            <div className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-blue-400" />
              Tracked Pages
            </div>
          </CardHeader>
          <CardBody className="p-0">
            {watchlist.pages.length === 0 ? (
              <div className="py-12 text-center">
                <Store className="w-12 h-12 mx-auto mb-4 text-slate-500 opacity-50" />
                <h3 className="text-lg font-medium text-slate-200 mb-2">
                  No pages in this watchlist
                </h3>
                <p className="text-slate-400">
                  Add pages from the page detail view to track them here
                </p>
              </div>
            ) : (
              <Table
                columns={columns}
                data={watchlist.pages}
                keyExtractor={(item) => item.page_id}
                emptyMessage="No pages found"
              />
            )}
          </CardBody>
        </Card>

        {/* Back button */}
        <div className="mt-8">
          <Link
            href="/watchlists"
            className="inline-flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to watchlists
          </Link>
        </div>
      </PageContent>
    </>
  );
}
