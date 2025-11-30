"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Store,
  Globe,
  ExternalLink,
  TrendingUp,
  Package,
  BarChart3,
  ArrowLeft,
  ShoppingBag,
  Tag,
  Calendar,
  RefreshCw,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  TierBadge,
  MatchBadge,
  Badge,
  Table,
  KpiTile,
  Button,
  ErrorState,
  LoadingState,
  type Column,
} from "@/components/ui";
import { Header, PageContent, Breadcrumbs, RefreshButton } from "@/components/layout";
import { ScoreChart } from "@/components/charts";
import {
  getPageDetails,
  getPageScore,
  getPageMetricsHistory,
  getPageProductInsights,
} from "@/lib/api";
import type {
  PageResponse,
  ShopScoreResponse,
  PageDailyMetrics,
  PageProductInsightsResponse,
  ProductInsightsEntry,
} from "@/lib/types/api";

/**
 * Page Detail Page
 *
 * Shows comprehensive information about a single page/shop including:
 * - Basic info and score
 * - Metrics history chart
 * - Product insights
 */
export default function PageDetailPage() {
  const params = useParams();
  const pageId = decodeURIComponent(params.pageId as string);

  const [page, setPage] = useState<PageResponse | null>(null);
  const [score, setScore] = useState<ShopScoreResponse | null>(null);
  const [metricsHistory, setMetricsHistory] = useState<PageDailyMetrics[]>([]);
  const [productInsights, setProductInsights] =
    useState<PageProductInsightsResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      const [pageData, scoreData, metricsData, insightsData] = await Promise.allSettled([
        getPageDetails(pageId),
        getPageScore(pageId),
        getPageMetricsHistory(pageId, { limit: 90 }),
        getPageProductInsights(pageId, { limit: 10, sort_by: "ads_count" }),
      ]);

      // Handle page data (required)
      if (pageData.status === "fulfilled") {
        setPage(pageData.value);
      } else {
        throw new Error("Page not found");
      }

      // Handle score (may not exist)
      if (scoreData.status === "fulfilled") {
        setScore(scoreData.value);
      }

      // Handle metrics history (may be empty)
      if (metricsData.status === "fulfilled") {
        setMetricsHistory(metricsData.value.metrics);
      }

      // Handle product insights (may be empty)
      if (insightsData.status === "fulfilled") {
        setProductInsights(insightsData.value);
      }
    } catch (err) {
      console.error("Error fetching page data:", err);
      setError(err instanceof Error ? err.message : "Failed to load page");
    } finally {
      setIsLoading(false);
    }
  }, [pageId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Product insights table columns
  const productColumns: Column<ProductInsightsEntry>[] = [
    {
      key: "product",
      header: "Product",
      render: (item) => (
        <div className="flex items-center gap-3">
          {item.product.image_url ? (
            <img
              src={item.product.image_url}
              alt={item.product.title}
              className="w-10 h-10 rounded-lg object-cover bg-slate-800"
            />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center">
              <ShoppingBag className="w-5 h-5 text-slate-500" />
            </div>
          )}
          <div className="min-w-0">
            <p className="font-medium text-slate-200 truncate max-w-[200px]">
              {item.product.title}
            </p>
            {item.product.price_min && (
              <p className="text-xs text-slate-500">
                {item.product.currency || "$"}
                {item.product.price_min.toFixed(2)}
                {item.product.price_max &&
                  item.product.price_max !== item.product.price_min &&
                  ` - ${item.product.price_max.toFixed(2)}`}
              </p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "ads_count",
      header: "Ads",
      render: (item) => (
        <span className="font-semibold text-slate-200">
          {item.insights.ads_count}
        </span>
      ),
      className: "w-20 text-center",
    },
    {
      key: "match_strength",
      header: "Match",
      render: (item) => {
        const strength = item.insights.has_strong_match
          ? "strong"
          : item.insights.match_score > 0.5
          ? "medium"
          : item.insights.match_score > 0
          ? "weak"
          : "none";
        return <MatchBadge strength={strength} size="sm" />;
      },
      className: "w-24",
    },
    {
      key: "promoted",
      header: "Status",
      render: (item) =>
        item.insights.is_promoted ? (
          <Badge variant="success" size="sm">
            Promoted
          </Badge>
        ) : (
          <Badge variant="default" size="sm">
            Not promoted
          </Badge>
        ),
      className: "w-28",
    },
  ];

  // Metrics history table columns (last 10 points)
  const metricsColumns: Column<PageDailyMetrics>[] = [
    {
      key: "date",
      header: "Date",
      render: (item) => (
        <span className="text-slate-300">
          {new Date(item.date).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: "score",
      header: "Score",
      render: (item) => (
        <span className="font-semibold text-slate-200">
          {item.shop_score.toFixed(1)}
        </span>
      ),
      className: "text-right",
    },
    {
      key: "tier",
      header: "Tier",
      render: (item) => <TierBadge tier={item.tier} size="sm" />,
    },
    {
      key: "ads",
      header: "Ads",
      render: (item) => (
        <span className="text-slate-300">{item.ads_count}</span>
      ),
      className: "text-right",
    },
    {
      key: "products",
      header: "Products",
      render: (item) => (
        <span className="text-slate-300">{item.products_count ?? "-"}</span>
      ),
      className: "text-right",
    },
  ];

  if (isLoading) {
    return (
      <>
        <Header
          title="Page Details"
          subtitle="Loading..."
        />
        <PageContent>
          <LoadingState message="Loading page details..." />
        </PageContent>
      </>
    );
  }

  if (error || !page) {
    return (
      <>
        <Header title="Page Details" />
        <PageContent>
          <ErrorState
            title="Page not found"
            message={error || "The requested page could not be found"}
            onRetry={fetchData}
          />
        </PageContent>
      </>
    );
  }

  return (
    <>
      <Header
        title={page.domain}
        subtitle={page.url}
        actions={
          <div className="flex items-center gap-2">
            <RefreshButton onClick={fetchData} isLoading={isLoading} />
            <a
              href={page.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-sm font-medium transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Visit Site
            </a>
          </div>
        }
      />
      <PageContent>
        {/* Breadcrumbs */}
        <div className="mb-6">
          <Breadcrumbs
            items={[
              { label: "Pages", href: "/pages" },
              { label: page.domain },
            ]}
          />
        </div>

        {/* Page Info Header */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Main Info Card */}
          <Card className="lg:col-span-2">
            <CardBody>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-xl bg-slate-800 flex items-center justify-center">
                    <Store className="w-8 h-8 text-slate-500" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-slate-100">
                      {page.domain}
                    </h2>
                    <p className="text-slate-400">{page.url}</p>
                    <div className="flex items-center gap-2 mt-2">
                      {page.is_shopify && (
                        <Badge variant="success" size="sm">
                          Shopify
                        </Badge>
                      )}
                      {page.country && (
                        <Badge variant="default" size="sm">
                          <Globe className="w-3 h-3 mr-1" />
                          {page.country}
                        </Badge>
                      )}
                      {page.currency && (
                        <Badge variant="default" size="sm">
                          {page.currency}
                        </Badge>
                      )}
                      {page.category && (
                        <Badge variant="default" size="sm">
                          <Tag className="w-3 h-3 mr-1" />
                          {page.category}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>

                {/* Score Display */}
                <div className="text-right">
                  <div className="text-4xl font-bold text-slate-100">
                    {score?.score.toFixed(1) ?? page.score.toFixed(1)}
                  </div>
                  <div className="mt-1">
                    <TierBadge tier={score?.tier ?? "XS"} size="lg" />
                  </div>
                </div>
              </div>

              {/* Score Components */}
              {score?.components && (
                <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-400">
                      {score.components.ads_activity.toFixed(0)}
                    </p>
                    <p className="text-xs text-slate-500">Ads Activity</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-400">
                      {score.components.shopify.toFixed(0)}
                    </p>
                    <p className="text-xs text-slate-500">Shopify</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-400">
                      {score.components.creative_quality.toFixed(0)}
                    </p>
                    <p className="text-xs text-slate-500">Creative</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-400">
                      {score.components.catalog.toFixed(0)}
                    </p>
                    <p className="text-xs text-slate-500">Catalog</p>
                  </div>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Quick Stats */}
          <div className="space-y-4">
            <KpiTile
              label="Active Ads"
              value={page.active_ads_count}
              icon={<TrendingUp className="w-5 h-5" />}
            />
            <KpiTile
              label="Products"
              value={page.product_count}
              icon={<Package className="w-5 h-5" />}
            />
            <KpiTile
              label="Last Scanned"
              value={
                page.last_scanned_at
                  ? new Date(page.last_scanned_at).toLocaleDateString()
                  : "Never"
              }
              icon={<Calendar className="w-5 h-5" />}
            />
          </div>
        </div>

        {/* Metrics History Section */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              Score Evolution (Last 90 Days)
            </div>
          </CardHeader>
          <CardBody>
            {metricsHistory.length > 0 ? (
              <>
                <ScoreChart data={metricsHistory} height={300} />

                {/* Recent metrics table */}
                <div className="mt-6 pt-6 border-t border-slate-800">
                  <h4 className="text-sm font-medium text-slate-400 mb-4">
                    Recent Data Points
                  </h4>
                  <Table
                    columns={metricsColumns}
                    data={metricsHistory.slice(-10).reverse()}
                    keyExtractor={(item) => item.date}
                    emptyMessage="No metrics data"
                  />
                </div>
              </>
            ) : (
              <div className="py-12 text-center text-slate-500">
                <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No metrics history available yet</p>
                <p className="text-sm mt-1">
                  Metrics are recorded daily by the snapshot task
                </p>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Product Insights Section */}
        <Card>
          <CardHeader
            action={
              productInsights && productInsights.total > 10 && (
                <span className="text-sm text-slate-500">
                  Showing top 10 of {productInsights.total} products
                </span>
              )
            }
          >
            <div className="flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-purple-400" />
              Product Insights
            </div>
          </CardHeader>
          <CardBody>
            {productInsights && productInsights.items.length > 0 ? (
              <>
                {/* Summary stats */}
                <div className="grid grid-cols-4 gap-4 mb-6 p-4 bg-slate-800/50 rounded-lg">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-slate-100">
                      {productInsights.summary.products_count}
                    </p>
                    <p className="text-xs text-slate-500">Total Products</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-400">
                      {productInsights.summary.products_with_ads_count}
                    </p>
                    <p className="text-xs text-slate-500">With Ads</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-400">
                      {(productInsights.summary.coverage_ratio * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-slate-500">Coverage</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-400">
                      {productInsights.summary.promoted_products_count}
                    </p>
                    <p className="text-xs text-slate-500">Promoted</p>
                  </div>
                </div>

                {/* Products table */}
                <Table
                  columns={productColumns}
                  data={productInsights.items}
                  keyExtractor={(item) => item.product.id}
                  emptyMessage="No product insights available"
                />
              </>
            ) : (
              <div className="py-12 text-center text-slate-500">
                <ShoppingBag className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No product insights available</p>
                <p className="text-sm mt-1">
                  {page.is_shopify
                    ? "Try syncing products first"
                    : "Product insights are only available for Shopify stores"}
                </p>
              </div>
            )}
          </CardBody>
        </Card>

        {/* Back button */}
        <div className="mt-8">
          <Link
            href="/pages"
            className="inline-flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to all pages
          </Link>
        </div>
      </PageContent>
    </>
  );
}
