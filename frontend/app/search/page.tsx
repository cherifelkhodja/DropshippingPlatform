"use client";

import { useState, useCallback } from "react";
import {
  Search,
  CheckCircle,
  XCircle,
  Loader2,
  FileSearch,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  Table,
  Button,
  Select,
  Badge,
  type Column,
} from "@/components/ui";
import { Header, PageContent } from "@/components/layout";
import { searchAdsByKeyword } from "@/lib/api";
import type { MultiKeywordSearchResult } from "@/lib/types/api";

// Country options for the dropdown
const COUNTRY_OPTIONS = [
  { value: "US", label: "United States" },
  { value: "FR", label: "France" },
  { value: "DE", label: "Germany" },
  { value: "GB", label: "United Kingdom" },
  { value: "ES", label: "Spain" },
  { value: "IT", label: "Italy" },
  { value: "NL", label: "Netherlands" },
  { value: "BE", label: "Belgium" },
  { value: "CH", label: "Switzerland" },
  { value: "AT", label: "Austria" },
  { value: "CA", label: "Canada" },
  { value: "AU", label: "Australia" },
  { value: "BR", label: "Brazil" },
  { value: "MX", label: "Mexico" },
  { value: "PL", label: "Poland" },
  { value: "PT", label: "Portugal" },
  { value: "SE", label: "Sweden" },
  { value: "NO", label: "Norway" },
  { value: "DK", label: "Denmark" },
  { value: "FI", label: "Finland" },
];

// Language options for the dropdown
const LANGUAGE_OPTIONS = [
  { value: "", label: "All Languages" },
  { value: "en", label: "English" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "es", label: "Spanish" },
  { value: "it", label: "Italian" },
  { value: "nl", label: "Dutch" },
  { value: "pt", label: "Portuguese" },
  { value: "pl", label: "Polish" },
  { value: "sv", label: "Swedish" },
  { value: "da", label: "Danish" },
  { value: "no", label: "Norwegian" },
  { value: "fi", label: "Finnish" },
];

/**
 * Search Page
 *
 * Allows searching for Meta Ads by keywords.
 * Supports multiple keywords (semicolon-separated), country (required), and language (optional).
 */
export default function SearchPage() {
  // Form state
  const [keywords, setKeywords] = useState("");
  const [country, setCountry] = useState("");
  const [language, setLanguage] = useState("");

  // Search state
  const [isSearching, setIsSearching] = useState(false);
  const [currentKeywordIndex, setCurrentKeywordIndex] = useState(0);
  const [results, setResults] = useState<MultiKeywordSearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  // Parse keywords from input (semicolon-separated)
  const parseKeywords = (input: string): string[] => {
    return input
      .split(";")
      .map((k) => k.trim())
      .filter((k) => k.length > 0);
  };

  // Execute search for all keywords
  const handleSearch = useCallback(async () => {
    const keywordList = parseKeywords(keywords);

    if (keywordList.length === 0) {
      return;
    }

    if (!country) {
      return;
    }

    setIsSearching(true);
    setResults([]);
    setHasSearched(true);

    const searchResults: MultiKeywordSearchResult[] = [];

    for (let i = 0; i < keywordList.length; i++) {
      const keyword = keywordList[i];
      setCurrentKeywordIndex(i);

      try {
        const result = await searchAdsByKeyword({
          keyword,
          country,
          language: language || undefined,
          limit: 1000,
        });

        searchResults.push({
          keyword,
          status: "success",
          result,
        });
      } catch (err) {
        searchResults.push({
          keyword,
          status: "error",
          error: err instanceof Error ? err.message : "Search failed",
        });
      }

      // Update results after each keyword (progressive display)
      setResults([...searchResults]);
    }

    setIsSearching(false);
  }, [keywords, country, language]);

  // Calculate totals
  const totals = results.reduce(
    (acc, r) => {
      if (r.status === "success" && r.result) {
        acc.totalAds += r.result.ads_found;
        acc.totalPages += r.result.pages_found;
        acc.totalNewPages += r.result.new_pages;
        acc.successCount++;
      } else {
        acc.errorCount++;
      }
      return acc;
    },
    { totalAds: 0, totalPages: 0, totalNewPages: 0, successCount: 0, errorCount: 0 }
  );

  // Table columns for results
  const columns: Column<MultiKeywordSearchResult>[] = [
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <div className="flex items-center gap-2">
          {item.status === "success" ? (
            <CheckCircle className="w-5 h-5 text-green-400" />
          ) : (
            <XCircle className="w-5 h-5 text-red-400" />
          )}
        </div>
      ),
      className: "w-16",
    },
    {
      key: "keyword",
      header: "Keyword",
      render: (item) => (
        <span className="font-medium text-slate-200">{item.keyword}</span>
      ),
    },
    {
      key: "ads_found",
      header: "Ads Found",
      render: (item) =>
        item.status === "success" && item.result ? (
          <Badge variant="info" size="sm">
            {item.result.ads_found.toLocaleString()}
          </Badge>
        ) : (
          <span className="text-slate-500">-</span>
        ),
      className: "w-32",
    },
    {
      key: "pages_found",
      header: "Pages Found",
      render: (item) =>
        item.status === "success" && item.result ? (
          <Badge variant="default" size="sm">
            {item.result.pages_found.toLocaleString()}
          </Badge>
        ) : (
          <span className="text-slate-500">-</span>
        ),
      className: "w-32",
    },
    {
      key: "new_pages",
      header: "New Pages",
      render: (item) =>
        item.status === "success" && item.result ? (
          <Badge variant="success" size="sm">
            {item.result.new_pages.toLocaleString()}
          </Badge>
        ) : (
          <span className="text-slate-500">-</span>
        ),
      className: "w-32",
    },
    {
      key: "scan_id",
      header: "Scan ID",
      render: (item) =>
        item.status === "success" && item.result ? (
          <span className="text-xs text-slate-500 font-mono">
            {item.result.scan_id.slice(0, 8)}...
          </span>
        ) : item.error ? (
          <span className="text-xs text-red-400">{item.error}</span>
        ) : (
          <span className="text-slate-500">-</span>
        ),
      className: "w-40",
    },
  ];

  const keywordList = parseKeywords(keywords);
  const isFormValid = keywordList.length > 0 && country !== "";

  return (
    <>
      <Header
        title="Meta Ads Search"
        subtitle="Search for active ads by keywords"
      />
      <PageContent>
        <div className="space-y-6">
          {/* Search Form */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Search className="w-5 h-5 text-blue-400" />
                Keyword Search
              </div>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                {/* Keywords Input */}
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1.5">
                    Keywords <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    placeholder="Enter keywords separated by semicolons (;)&#10;Example: dropshipping; ecommerce; online store"
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    disabled={isSearching}
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    {keywordList.length} keyword{keywordList.length !== 1 ? "s" : ""} detected
                  </p>
                </div>

                {/* Country and Language Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-1.5">
                      Country <span className="text-red-400">*</span>
                    </label>
                    <Select
                      options={COUNTRY_OPTIONS}
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                      placeholder="Select a country"
                      disabled={isSearching}
                    />
                  </div>
                  <div>
                    <Select
                      label="Language (optional)"
                      options={LANGUAGE_OPTIONS}
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      placeholder="All languages"
                      disabled={isSearching}
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <div className="flex items-center justify-between pt-2">
                  <div className="text-sm text-slate-500">
                    {isSearching && (
                      <span className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Searching keyword {currentKeywordIndex + 1} of {keywordList.length}...
                      </span>
                    )}
                  </div>
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={handleSearch}
                    disabled={!isFormValid || isSearching}
                    isLoading={isSearching}
                    className="flex items-center gap-2"
                  >
                    <Search className="w-4 h-4" />
                    Search Ads
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Results Summary */}
          {hasSearched && results.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <FileSearch className="w-5 h-5 text-green-400" />
                  Search Results Summary
                </div>
              </CardHeader>
              <CardBody>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                  <div className="bg-slate-800 rounded-lg p-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider">Keywords</p>
                    <p className="text-2xl font-bold text-slate-100">{results.length}</p>
                  </div>
                  <div className="bg-slate-800 rounded-lg p-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider">Total Ads</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {totals.totalAds.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-slate-800 rounded-lg p-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider">Pages Found</p>
                    <p className="text-2xl font-bold text-slate-100">
                      {totals.totalPages.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-slate-800 rounded-lg p-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider">New Pages</p>
                    <p className="text-2xl font-bold text-green-400">
                      {totals.totalNewPages.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-slate-800 rounded-lg p-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider">Success Rate</p>
                    <p className="text-2xl font-bold text-slate-100">
                      {results.length > 0
                        ? Math.round((totals.successCount / results.length) * 100)
                        : 0}%
                    </p>
                  </div>
                </div>

                {/* Results Table */}
                <Table
                  columns={columns}
                  data={results}
                  keyExtractor={(item) => item.keyword}
                  emptyMessage="No results"
                />
              </CardBody>
            </Card>
          )}

          {/* Empty State */}
          {hasSearched && results.length === 0 && !isSearching && (
            <Card>
              <CardBody>
                <div className="py-12 text-center">
                  <Search className="w-12 h-12 mx-auto mb-4 text-slate-500 opacity-50" />
                  <h3 className="text-lg font-medium text-slate-200 mb-2">
                    No results found
                  </h3>
                  <p className="text-slate-400">
                    Try different keywords or adjust your filters
                  </p>
                </div>
              </CardBody>
            </Card>
          )}

          {/* Instructions */}
          {!hasSearched && (
            <Card>
              <CardBody>
                <div className="py-8">
                  <h3 className="text-lg font-medium text-slate-200 mb-4">
                    How to use
                  </h3>
                  <ul className="space-y-2 text-slate-400">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">1.</span>
                      <span>
                        Enter your keywords in the text area, separated by semicolons (;).
                        Example: <code className="text-slate-300 bg-slate-800 px-1 rounded">dropshipping; ecommerce; online store</code>
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">2.</span>
                      <span>
                        Select a target country (required). This determines which ads are shown based on reach.
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">3.</span>
                      <span>
                        Optionally select a language to filter ads by language.
                      </span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-400 mt-0.5">4.</span>
                      <span>
                        Click &quot;Search Ads&quot; to start. Each keyword will be searched separately with full pagination (up to 1000 ads per keyword).
                      </span>
                    </li>
                  </ul>
                </div>
              </CardBody>
            </Card>
          )}
        </div>
      </PageContent>
    </>
  );
}
