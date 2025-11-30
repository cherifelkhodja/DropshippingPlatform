/**
 * TypeScript types mirroring the backend Pydantic schemas.
 * These types ensure type-safe API communication.
 */

// =============================================================================
// Common Types
// =============================================================================

export type Tier = "XXL" | "XL" | "L" | "M" | "S" | "XS";

export type MatchStrength = "strong" | "medium" | "weak" | "none";

export type ProductInsightsSortBy = "ads_count" | "match_score" | "last_seen_at";

// =============================================================================
// Page Types
// =============================================================================

export interface PageResponse {
  id: string;
  url: string;
  domain: string;
  country: string | null;
  language: string | null;
  currency: string | null;
  category: string | null;
  is_shopify: boolean;
  product_count: number;
  active_ads_count: number;
  total_ads_count: number;
  status: string;
  score: number;
  first_seen_at: string | null;
  last_scanned_at: string | null;
}

export interface PageListResponse {
  items: PageResponse[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// =============================================================================
// Scoring & Ranking Types
// =============================================================================

export interface ScoreComponents {
  ads_activity: number;
  shopify: number;
  creative_quality: number;
  catalog: number;
}

export interface ShopScoreResponse {
  page_id: string;
  score: number;
  tier: Tier;
  components: ScoreComponents;
  computed_at: string;
}

export interface TopShopEntry {
  rank: number;
  page_id: string;
  domain: string;
  score: number;
  tier: Tier;
  computed_at: string;
}

export interface TopShopsResponse {
  items: TopShopEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface RankedShopEntry {
  page_id: string;
  score: number;
  tier: Tier;
  url: string | null;
  country: string | null;
  name: string | null;
}

export interface RankedShopsResponse {
  items: RankedShopEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface RankedShopsFilters {
  limit?: number;
  offset?: number;
  tier?: Tier;
  min_score?: number;
  country?: string;
}

// =============================================================================
// Metrics Types (Sprint 7)
// =============================================================================

export interface PageDailyMetrics {
  date: string;
  ads_count: number;
  shop_score: number;
  tier: Tier;
  products_count: number | null;
}

export interface PageMetricsHistoryResponse {
  page_id: string;
  metrics: PageDailyMetrics[];
}

export interface MetricsHistoryParams {
  date_from?: string;
  date_to?: string;
  limit?: number;
}

// =============================================================================
// Product Types (Sprint 6)
// =============================================================================

export interface ProductResponse {
  id: string;
  page_id: string;
  handle: string;
  title: string;
  url: string;
  price_min: number | null;
  price_max: number | null;
  currency: string | null;
  available: boolean;
  tags: string[];
  vendor: string | null;
  image_url: string | null;
  product_type: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductListResponse {
  items: ProductResponse[];
  total: number;
  page_id: string;
  limit: number;
  offset: number;
}

// =============================================================================
// Product Insights Types (Sprint 6)
// =============================================================================

export interface AdMatchResponse {
  ad_id: string;
  score: number;
  strength: MatchStrength;
  reasons: string[];
  ad_title: string | null;
  ad_link_url: string | null;
  ad_is_active: boolean;
}

export interface ProductInsightsData {
  ads_count: number;
  distinct_creatives_count: number;
  match_score: number;
  has_strong_match: boolean;
  is_promoted: boolean;
  strong_matches_count: number;
  medium_matches_count: number;
  weak_matches_count: number;
  first_seen_at: string | null;
  last_seen_at: string | null;
  match_reasons: string[];
  matched_ads: AdMatchResponse[];
}

export interface ProductInsightsEntry {
  product: ProductResponse;
  insights: ProductInsightsData;
}

export interface PageProductInsightsSummary {
  page_id: string;
  products_count: number;
  products_with_ads_count: number;
  promoted_products_count: number;
  total_ads_analyzed: number;
  coverage_ratio: number;
  promotion_ratio: number;
  computed_at: string;
}

export interface PageProductInsightsResponse {
  summary: PageProductInsightsSummary;
  items: ProductInsightsEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface ProductInsightsParams {
  limit?: number;
  offset?: number;
  sort_by?: ProductInsightsSortBy;
}

// =============================================================================
// Alert Types (Sprint 5)
// =============================================================================

export type AlertType =
  | "NEW_ADS_BOOST"
  | "SCORE_JUMP"
  | "SCORE_DROP"
  | "TIER_UP"
  | "TIER_DOWN";

export type AlertSeverity = "info" | "warning" | "critical";

export interface AlertResponse {
  id: string;
  page_id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  message: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export interface AlertListResponse {
  items: AlertResponse[];
  count: number;
}

// =============================================================================
// Error Types
// =============================================================================

export interface ApiError {
  detail: string;
  status_code?: number;
}

// =============================================================================
// Dashboard Stats Types (computed client-side or from API)
// =============================================================================

export interface DashboardStats {
  totalPages: number;
  shopifyPages: number;
  tierABPages: number; // XXL + XL tiers
  lastSnapshotDate: string | null;
}

// =============================================================================
// Watchlist Types (Sprint 5 + Sprint 8.1)
// =============================================================================

export interface WatchlistResponse {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  is_active: boolean;
}

export interface WatchlistListResponse {
  items: WatchlistResponse[];
  count: number;
}

export interface WatchlistItemResponse {
  id: string;
  watchlist_id: string;
  page_id: string;
  created_at: string;
}

export interface WatchlistItemListResponse {
  items: WatchlistItemResponse[];
  count: number;
}

export interface WatchlistCreateRequest {
  name: string;
  description?: string | null;
}

export interface WatchlistItemRequest {
  page_id: string;
}

export interface RescoreWatchlistResponse {
  watchlist_id: string;
  tasks_dispatched: number;
  message: string;
}

// Extended Watchlist Types (Sprint 8.1) - with page details
export interface WatchlistPageInfo {
  page_id: string;
  page_name: string;
  url: string;
  country: string | null;
  is_shopify: boolean;
  shop_score: number;
  tier: Tier;
  active_ads_count: number;
  added_at: string;
}

export interface WatchlistWithDetails {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  is_active: boolean;
  pages_count: number;
  pages: WatchlistPageInfo[];
}

export interface WatchlistSummary {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  is_active: boolean;
  pages_count: number;
}

export interface WatchlistSummaryListResponse {
  items: WatchlistSummary[];
  count: number;
}

export interface PageWatchlistsResponse {
  page_id: string;
  watchlists: WatchlistResponse[];
  count: number;
}

// =============================================================================
// Monitoring Types (Sprint 8.1)
// =============================================================================

export interface MonitoringSummary {
  total_pages: number;
  pages_with_scores: number;
  alerts_last_24h: number;
  alerts_last_7d: number;
  last_metrics_snapshot_date: string | null;
  metrics_snapshots_count: number;
  generated_at: string;
}

// =============================================================================
// Admin Types (for Monitoring page)
// =============================================================================

export interface AdminPageResponse {
  page_id: string;
  page_name: string;
  country: string | null;
  is_shopify: boolean;
  ads_count: number;
  product_count: number;
  state: string;
  last_scan_at: string | null;
}

export interface AdminPageListResponse {
  items: AdminPageResponse[];
  total: number;
  offset: number;
  limit: number;
}

export interface AdminKeywordRunResponse {
  keyword: string;
  country: string;
  created_at: string;
  total_ads_found: number;
  total_pages_found: number;
  scan_id: string;
}

export interface AdminKeywordListResponse {
  items: AdminKeywordRunResponse[];
  total: number;
}

export interface AdminScanResponse {
  id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  page_id: string | null;
  result_summary: string | null;
}

export interface AdminScanListResponse {
  items: AdminScanResponse[];
  total: number;
  offset: number;
  limit: number;
}
