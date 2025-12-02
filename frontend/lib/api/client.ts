/**
 * API Client for the Dropshipping Platform Backend.
 *
 * This module provides a typed HTTP client for communicating with the FastAPI backend.
 * All API calls go through this layer for consistent error handling and typing.
 */

import {
  PageResponse,
  PageListResponse,
  TopShopsResponse,
  RankedShopsResponse,
  RankedShopsFilters,
  ShopScoreResponse,
  PageMetricsHistoryResponse,
  MetricsHistoryParams,
  ProductListResponse,
  PageProductInsightsResponse,
  ProductInsightsParams,
  ProductInsightsEntry,
  AlertListResponse,
  ApiError,
  // Watchlist Types (Sprint 8.1)
  WatchlistResponse,
  WatchlistListResponse,
  WatchlistWithDetails,
  WatchlistSummaryListResponse,
  WatchlistCreateRequest,
  WatchlistItemResponse,
  RescoreWatchlistResponse,
  PageWatchlistsResponse,
  // Monitoring Types (Sprint 8.1)
  MonitoringSummary,
  AdminPageListResponse,
  AdminKeywordListResponse,
  AdminScanListResponse,
  // Creative Insights Types (Sprint 9)
  PageCreativeInsightsResponse,
  CreativeAnalysisResponse,
  AnalyzeCreativesResponse,
} from "@/lib/types/api";

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

// =============================================================================
// Error Handling
// =============================================================================

export class ApiClientError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "Unknown error";
    try {
      const errorBody: ApiError = await response.json();
      detail = errorBody.detail || detail;
    } catch {
      detail = response.statusText;
    }
    throw new ApiClientError(
      `API Error: ${response.status}`,
      response.status,
      detail
    );
  }
  return response.json();
}

// =============================================================================
// Generic Fetch Helper
// =============================================================================

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    "Content-Type": "application/json",
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  return handleResponse<T>(response);
}

// =============================================================================
// Query String Builder
// =============================================================================

function buildQueryString(params: Record<string, unknown>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.append(key, String(value));
    }
  });
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}

// =============================================================================
// Page API Functions
// =============================================================================

/**
 * Get top-ranked pages/shops.
 * Uses GET /pages/top endpoint.
 */
export async function getTopPages(
  limit: number = 20,
  offset: number = 0
): Promise<TopShopsResponse> {
  const query = buildQueryString({ limit, offset });
  return apiFetch<TopShopsResponse>(`/pages/top${query}`);
}

/**
 * Get ranked pages with optional filters.
 * Uses GET /pages/ranked endpoint.
 */
export async function getRankedPages(
  filters: RankedShopsFilters = {}
): Promise<RankedShopsResponse> {
  const query = buildQueryString(filters);
  return apiFetch<RankedShopsResponse>(`/pages/ranked${query}`);
}

/**
 * Get details of a specific page.
 * Uses GET /pages/{page_id} endpoint.
 */
export async function getPageDetails(pageId: string): Promise<PageResponse> {
  return apiFetch<PageResponse>(`/pages/${encodeURIComponent(pageId)}`);
}

/**
 * Get the computed score for a page.
 * Uses GET /pages/{page_id}/score endpoint.
 */
export async function getPageScore(pageId: string): Promise<ShopScoreResponse> {
  return apiFetch<ShopScoreResponse>(
    `/pages/${encodeURIComponent(pageId)}/score`
  );
}

/**
 * List all pages with optional filters.
 * Uses GET /pages endpoint.
 */
export async function listPages(params: {
  country?: string;
  is_shopify?: boolean;
  min_active_ads?: number;
  page?: number;
  page_size?: number;
}): Promise<PageListResponse> {
  const query = buildQueryString(params);
  return apiFetch<PageListResponse>(`/pages${query}`);
}

// =============================================================================
// Metrics API Functions (Sprint 7)
// =============================================================================

/**
 * Get metrics history for a page (time series data).
 * Uses GET /pages/{page_id}/metrics/history endpoint.
 */
export async function getPageMetricsHistory(
  pageId: string,
  params: MetricsHistoryParams = {}
): Promise<PageMetricsHistoryResponse> {
  const query = buildQueryString(params);
  return apiFetch<PageMetricsHistoryResponse>(
    `/pages/${encodeURIComponent(pageId)}/metrics/history${query}`
  );
}

// =============================================================================
// Product API Functions (Sprint 6)
// =============================================================================

/**
 * Get products for a page.
 * Uses GET /pages/{page_id}/products endpoint.
 */
export async function getPageProducts(
  pageId: string,
  limit: number = 50,
  offset: number = 0
): Promise<ProductListResponse> {
  const query = buildQueryString({ limit, offset });
  return apiFetch<ProductListResponse>(
    `/pages/${encodeURIComponent(pageId)}/products${query}`
  );
}

/**
 * Get product insights for a page.
 * Uses GET /pages/{page_id}/products/insights endpoint.
 */
export async function getPageProductInsights(
  pageId: string,
  params: ProductInsightsParams = {}
): Promise<PageProductInsightsResponse> {
  const query = buildQueryString(params);
  return apiFetch<PageProductInsightsResponse>(
    `/pages/${encodeURIComponent(pageId)}/products/insights${query}`
  );
}

/**
 * Get insights for a specific product.
 * Uses GET /pages/{page_id}/products/{product_id}/insights endpoint.
 */
export async function getProductInsights(
  pageId: string,
  productId: string
): Promise<ProductInsightsEntry> {
  return apiFetch<ProductInsightsEntry>(
    `/pages/${encodeURIComponent(pageId)}/products/${encodeURIComponent(
      productId
    )}/insights`
  );
}

// =============================================================================
// Alert API Functions (Sprint 5)
// =============================================================================

/**
 * Get alerts for a specific page.
 * Uses GET /alerts/{page_id} endpoint.
 */
export async function getPageAlerts(
  pageId: string,
  limit: number = 50,
  offset: number = 0
): Promise<AlertListResponse> {
  const query = buildQueryString({ limit, offset });
  return apiFetch<AlertListResponse>(
    `/alerts/${encodeURIComponent(pageId)}${query}`
  );
}

/**
 * Get recent alerts across all pages.
 * Uses GET /alerts endpoint.
 */
export async function getRecentAlerts(
  limit: number = 100
): Promise<AlertListResponse> {
  const query = buildQueryString({ limit });
  return apiFetch<AlertListResponse>(`/alerts${query}`);
}

// =============================================================================
// Stats API Functions (Dashboard)
// =============================================================================

/**
 * Get dashboard statistics.
 * This aggregates data from multiple endpoints.
 * TODO: Create a dedicated backend endpoint for dashboard stats.
 */
export async function getDashboardStats(): Promise<{
  totalPages: number;
  shopifyPages: number;
  tierABPages: number;
  lastSnapshotDate: string | null;
}> {
  // For now, we aggregate from available endpoints
  // In a production scenario, this should be a single backend endpoint
  try {
    const [allPages, topTierPages] = await Promise.all([
      listPages({ page_size: 1 }), // Just to get total count
      getRankedPages({ tier: "XXL", limit: 1 }), // Get XXL tier count
    ]);

    // TODO: Backend should expose these stats directly
    // For now, we return partial data
    return {
      totalPages: allPages.total,
      shopifyPages: 0, // TODO: Backend needs endpoint for shopify count
      tierABPages: topTierPages.total, // XXL tier count
      lastSnapshotDate: null, // TODO: Backend needs endpoint for last snapshot date
    };
  } catch (error) {
    console.error("Error fetching dashboard stats:", error);
    return {
      totalPages: 0,
      shopifyPages: 0,
      tierABPages: 0,
      lastSnapshotDate: null,
    };
  }
}

// =============================================================================
// Watchlist API Functions (Sprint 8.1)
// =============================================================================

/**
 * Get list of watchlists with page counts.
 * Uses GET /watchlists/summary endpoint.
 */
export async function getWatchlists(
  limit: number = 50,
  offset: number = 0
): Promise<WatchlistSummaryListResponse> {
  const query = buildQueryString({ limit, offset });
  return apiFetch<WatchlistSummaryListResponse>(`/watchlists/summary${query}`);
}

/**
 * Get a single watchlist by ID.
 * Uses GET /watchlists/{id} endpoint.
 */
export async function getWatchlist(watchlistId: string): Promise<WatchlistResponse> {
  return apiFetch<WatchlistResponse>(`/watchlists/${encodeURIComponent(watchlistId)}`);
}

/**
 * Get a watchlist with full page details.
 * Uses GET /watchlists/{id}/details endpoint.
 */
export async function getWatchlistWithDetails(
  watchlistId: string
): Promise<WatchlistWithDetails> {
  return apiFetch<WatchlistWithDetails>(
    `/watchlists/${encodeURIComponent(watchlistId)}/details`
  );
}

/**
 * Create a new watchlist.
 * Uses POST /watchlists endpoint.
 */
export async function createWatchlist(
  data: WatchlistCreateRequest
): Promise<WatchlistResponse> {
  return apiFetch<WatchlistResponse>("/watchlists", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Add a page to a watchlist.
 * Uses POST /watchlists/{id}/items endpoint.
 */
export async function addPageToWatchlist(
  watchlistId: string,
  pageId: string
): Promise<WatchlistItemResponse> {
  return apiFetch<WatchlistItemResponse>(
    `/watchlists/${encodeURIComponent(watchlistId)}/items`,
    {
      method: "POST",
      body: JSON.stringify({ page_id: pageId }),
    }
  );
}

/**
 * Remove a page from a watchlist.
 * Uses DELETE /watchlists/{id}/items/{page_id} endpoint.
 */
export async function removePageFromWatchlist(
  watchlistId: string,
  pageId: string
): Promise<void> {
  await fetch(
    `${API_BASE_URL}/watchlists/${encodeURIComponent(
      watchlistId
    )}/items/${encodeURIComponent(pageId)}`,
    { method: "DELETE" }
  );
}

/**
 * Trigger rescore for all pages in a watchlist.
 * Uses POST /watchlists/{id}/scan_now endpoint.
 */
export async function rescoreWatchlist(
  watchlistId: string
): Promise<RescoreWatchlistResponse> {
  return apiFetch<RescoreWatchlistResponse>(
    `/watchlists/${encodeURIComponent(watchlistId)}/scan_now`,
    { method: "POST" }
  );
}

/**
 * Get watchlists that contain a specific page.
 * Uses GET /watchlists/by-page/{page_id} endpoint.
 */
export async function getPageWatchlists(
  pageId: string
): Promise<PageWatchlistsResponse> {
  return apiFetch<PageWatchlistsResponse>(
    `/watchlists/by-page/${encodeURIComponent(pageId)}`
  );
}

// =============================================================================
// Monitoring API Functions (Sprint 8.1)
// =============================================================================

/**
 * Get system monitoring summary.
 * Uses GET /admin/monitoring/summary endpoint.
 */
export async function getMonitoringSummary(): Promise<MonitoringSummary> {
  return apiFetch<MonitoringSummary>("/admin/monitoring/summary");
}

/**
 * Get list of active pages for admin monitoring.
 * Uses GET /admin/pages/active endpoint.
 */
export async function getAdminPages(params: {
  country?: string;
  is_shopify?: boolean;
  min_ads?: number;
  max_ads?: number;
  state?: string;
  offset?: number;
  limit?: number;
}): Promise<AdminPageListResponse> {
  const query = buildQueryString(params);
  return apiFetch<AdminPageListResponse>(`/admin/pages/active${query}`);
}

/**
 * Get recent keyword runs for admin monitoring.
 * Uses GET /admin/keywords/recent endpoint.
 */
export async function getAdminKeywords(
  limit: number = 50
): Promise<AdminKeywordListResponse> {
  const query = buildQueryString({ limit });
  return apiFetch<AdminKeywordListResponse>(`/admin/keywords/recent${query}`);
}

/**
 * Get scans for admin monitoring.
 * Uses GET /admin/scans endpoint.
 */
export async function getAdminScans(params: {
  status?: string;
  since?: string;
  page_id?: string;
  offset?: number;
  limit?: number;
}): Promise<AdminScanListResponse> {
  const query = buildQueryString(params);
  return apiFetch<AdminScanListResponse>(`/admin/scans${query}`);
}

/**
 * Trigger daily metrics snapshot.
 * Uses POST /admin/metrics/daily-snapshot endpoint.
 */
export async function triggerDailySnapshot(
  snapshotDate?: string
): Promise<{ status: string; task_id: string; snapshot_date: string }> {
  return apiFetch<{ status: string; task_id: string; snapshot_date: string }>(
    "/admin/metrics/daily-snapshot",
    {
      method: "POST",
      body: JSON.stringify({ snapshot_date: snapshotDate }),
    }
  );
}

// =============================================================================
// Creative Insights (Sprint 9)
// =============================================================================

/**
 * Get creative insights for a page.
 * Uses GET /pages/{pageId}/creatives/insights endpoint.
 */
export async function getPageCreativeInsights(
  pageId: string
): Promise<PageCreativeInsightsResponse> {
  return apiFetch<PageCreativeInsightsResponse>(
    `/pages/${encodeURIComponent(pageId)}/creatives/insights`
  );
}

/**
 * Get creative analysis for a specific ad.
 * Uses GET /ads/{adId}/analysis endpoint.
 */
export async function getAdCreativeAnalysis(
  adId: string
): Promise<CreativeAnalysisResponse> {
  return apiFetch<CreativeAnalysisResponse>(
    `/ads/${encodeURIComponent(adId)}/analysis`
  );
}

/**
 * Trigger creative analysis for a page (Admin).
 * Uses POST /admin/pages/{pageId}/creatives/analyze endpoint.
 */
export async function triggerCreativeAnalysis(
  pageId: string,
  adminApiKey?: string
): Promise<AnalyzeCreativesResponse> {
  const headers: Record<string, string> = {};
  if (adminApiKey) {
    headers["X-Admin-Api-Key"] = adminApiKey;
  }

  return apiFetch<AnalyzeCreativesResponse>(
    `/admin/pages/${encodeURIComponent(pageId)}/creatives/analyze`,
    {
      method: "POST",
      headers,
    }
  );
}

// =============================================================================
// Keyword Search API Functions
// =============================================================================

export interface KeywordSearchParams {
  keyword: string;
  country: string;
  language?: string;
  limit?: number;
}

export interface KeywordSearchResult {
  scan_id: string;
  keyword: string;
  country: string;
  ads_found: number;
  pages_found: number;
  new_pages: number;
}

/**
 * Search for ads by keyword via Meta Ads Library API.
 * Uses POST /keywords/search endpoint.
 */
export async function searchByKeyword(
  params: KeywordSearchParams
): Promise<KeywordSearchResult> {
  return apiFetch<KeywordSearchResult>("/keywords/search", {
    method: "POST",
    body: JSON.stringify({
      keyword: params.keyword,
      country: params.country,
      language: params.language,
      limit: params.limit || 1000,
    }),
  });
}
