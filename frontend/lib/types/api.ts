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
