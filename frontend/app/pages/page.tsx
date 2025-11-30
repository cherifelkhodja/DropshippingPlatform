"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Store,
  ChevronRight,
  Filter,
  X,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  Table,
  TierBadge,
  Pagination,
  Select,
  Input,
  Button,
  ErrorState,
  Badge,
  type Column,
} from "@/components/ui";
import { Header, PageContent, RefreshButton } from "@/components/layout";
import { getRankedPages } from "@/lib/api";
import type { RankedShopEntry, Tier, RankedShopsFilters } from "@/lib/types/api";

// Available tier options
const TIER_OPTIONS = [
  { value: "", label: "All Tiers" },
  { value: "XXL", label: "XXL (85-100)" },
  { value: "XL", label: "XL (70-85)" },
  { value: "L", label: "L (55-70)" },
  { value: "M", label: "M (40-55)" },
  { value: "S", label: "S (25-40)" },
  { value: "XS", label: "XS (0-25)" },
];

// Common country codes (can be expanded)
const COUNTRY_OPTIONS = [
  { value: "", label: "All Countries" },
  { value: "US", label: "United States" },
  { value: "FR", label: "France" },
  { value: "GB", label: "United Kingdom" },
  { value: "DE", label: "Germany" },
  { value: "ES", label: "Spain" },
  { value: "IT", label: "Italy" },
  { value: "CA", label: "Canada" },
  { value: "AU", label: "Australia" },
  { value: "NL", label: "Netherlands" },
  { value: "BE", label: "Belgium" },
];

const PAGE_SIZE = 20;

/**
 * Pages List Page
 *
 * Displays a filterable list of all tracked pages/shops.
 */
export default function PagesListPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Parse initial filters from URL
  const initialPage = parseInt(searchParams.get("page") || "1", 10);
  const initialTier = (searchParams.get("tier") as Tier) || undefined;
  const initialCountry = searchParams.get("country") || undefined;

  const [pages, setPages] = useState<RankedShopEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [tierFilter, setTierFilter] = useState<string>(initialTier || "");
  const [countryFilter, setCountryFilter] = useState<string>(
    initialCountry || ""
  );
  const [searchQuery, setSearchQuery] = useState("");

  // Build filters object
  const buildFilters = useCallback((): RankedShopsFilters => {
    return {
      limit: PAGE_SIZE,
      offset: (currentPage - 1) * PAGE_SIZE,
      tier: tierFilter as Tier | undefined,
      country: countryFilter || undefined,
    };
  }, [currentPage, tierFilter, countryFilter]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const filters = buildFilters();
      const response = await getRankedPages(filters);
      setPages(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error("Error fetching pages:", err);
      setError(err instanceof Error ? err.message : "Failed to load pages");
    } finally {
      setIsLoading(false);
    }
  }, [buildFilters]);

  // Update URL params when filters change
  const updateUrlParams = useCallback(() => {
    const params = new URLSearchParams();
    if (currentPage > 1) params.set("page", currentPage.toString());
    if (tierFilter) params.set("tier", tierFilter);
    if (countryFilter) params.set("country", countryFilter);

    const queryString = params.toString();
    router.push(queryString ? `/pages?${queryString}` : "/pages", {
      scroll: false,
    });
  }, [currentPage, tierFilter, countryFilter, router]);

  // Fetch on mount and filter changes
  useEffect(() => {
    fetchData();
    updateUrlParams();
  }, [fetchData, updateUrlParams]);

  // Handle filter changes
  const handleTierChange = (value: string) => {
    setTierFilter(value);
    setCurrentPage(1);
  };

  const handleCountryChange = (value: string) => {
    setCountryFilter(value);
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setTierFilter("");
    setCountryFilter("");
    setSearchQuery("");
    setCurrentPage(1);
  };

  const hasActiveFilters = tierFilter || countryFilter || searchQuery;

  // Filter pages by search query (client-side)
  const filteredPages = searchQuery
    ? pages.filter(
        (p) =>
          p.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.url?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : pages;

  const totalPages = Math.ceil(total / PAGE_SIZE);

  // Table columns
  const columns: Column<RankedShopEntry>[] = [
    {
      key: "name",
      header: "Page / Shop",
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center shrink-0">
            <Store className="w-5 h-5 text-slate-500" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-slate-200 truncate">
              {item.name || "Unknown"}
            </p>
            {item.url && (
              <p className="text-xs text-slate-500 truncate max-w-[250px]">
                {item.url}
              </p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "country",
      header: "Country",
      render: (item) => (
        <span className="text-slate-300">
          {item.country || "-"}
        </span>
      ),
      className: "w-24",
    },
    {
      key: "score",
      header: "Score",
      render: (item) => (
        <span className="font-semibold text-slate-200">
          {item.score.toFixed(1)}
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
      key: "actions",
      header: "",
      render: (item) => (
        <Link
          href={`/pages/${encodeURIComponent(item.page_id)}`}
          className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
        >
          Details
          <ChevronRight className="w-4 h-4" />
        </Link>
      ),
      className: "w-24",
    },
  ];

  if (error) {
    return (
      <>
        <Header title="Pages" subtitle="All tracked pages and shops" />
        <PageContent>
          <ErrorState
            title="Failed to load pages"
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
        title="Pages"
        subtitle={`${total} pages tracked`}
        actions={<RefreshButton onClick={fetchData} isLoading={isLoading} />}
      />
      <PageContent>
        {/* Filters */}
        <Card className="mb-6">
          <CardBody>
            <div className="flex flex-wrap items-end gap-4">
              <div className="w-48">
                <Input
                  label="Search"
                  placeholder="Search by name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="w-40">
                <Select
                  label="Tier"
                  options={TIER_OPTIONS}
                  value={tierFilter}
                  onChange={(e) => handleTierChange(e.target.value)}
                />
              </div>
              <div className="w-48">
                <Select
                  label="Country"
                  options={COUNTRY_OPTIONS}
                  value={countryFilter}
                  onChange={(e) => handleCountryChange(e.target.value)}
                />
              </div>
              {hasActiveFilters && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFilters}
                  className="flex items-center gap-1"
                >
                  <X className="w-4 h-4" />
                  Clear filters
                </Button>
              )}
            </div>

            {/* Active filters badges */}
            {hasActiveFilters && (
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-800">
                <Filter className="w-4 h-4 text-slate-500" />
                <span className="text-sm text-slate-500">Active filters:</span>
                {tierFilter && (
                  <Badge variant="info" size="sm">
                    Tier: {tierFilter}
                  </Badge>
                )}
                {countryFilter && (
                  <Badge variant="info" size="sm">
                    Country: {countryFilter}
                  </Badge>
                )}
                {searchQuery && (
                  <Badge variant="info" size="sm">
                    Search: {searchQuery}
                  </Badge>
                )}
              </div>
            )}
          </CardBody>
        </Card>

        {/* Pages Table */}
        <Card>
          <CardBody className="p-0">
            <Table
              columns={columns}
              data={filteredPages}
              keyExtractor={(item) => item.page_id}
              isLoading={isLoading}
              emptyMessage={
                hasActiveFilters
                  ? "No pages match your filters"
                  : "No pages found"
              }
            />
          </CardBody>
        </Card>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-6">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          </div>
        )}
      </PageContent>
    </>
  );
}
