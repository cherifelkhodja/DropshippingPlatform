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
