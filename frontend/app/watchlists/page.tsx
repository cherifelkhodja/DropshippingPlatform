"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Eye,
  ChevronRight,
  Plus,
  ListChecks,
  Store,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardBody,
  Table,
  Button,
  ErrorState,
  LoadingState,
  Badge,
  type Column,
} from "@/components/ui";
import { Header, PageContent, RefreshButton } from "@/components/layout";
import { getWatchlists, createWatchlist } from "@/lib/api";
import type { WatchlistSummary } from "@/lib/types/api";

/**
 * Watchlists Page
 *
 * Displays a list of all watchlists with their page counts.
 * Allows creating new watchlists and navigating to details.
 */
export default function WatchlistsPage() {
  const [watchlists, setWatchlists] = useState<WatchlistSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState("");
  const [newWatchlistDescription, setNewWatchlistDescription] = useState("");

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getWatchlists();
      setWatchlists(response.items);
    } catch (err) {
      console.error("Error fetching watchlists:", err);
      setError(err instanceof Error ? err.message : "Failed to load watchlists");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateWatchlist = async () => {
    if (!newWatchlistName.trim()) return;

    setIsCreating(true);
    try {
      await createWatchlist({
        name: newWatchlistName.trim(),
        description: newWatchlistDescription.trim() || null,
      });
      setShowCreateModal(false);
      setNewWatchlistName("");
      setNewWatchlistDescription("");
      await fetchData();
    } catch (err) {
      console.error("Error creating watchlist:", err);
    } finally {
      setIsCreating(false);
    }
  };

  // Table columns
  const columns: Column<WatchlistSummary>[] = [
    {
      key: "name",
      header: "Watchlist",
      render: (item) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center shrink-0">
            <Eye className="w-5 h-5 text-blue-400" />
          </div>
          <div className="min-w-0">
            <p className="font-medium text-slate-200">
              {item.name}
            </p>
            {item.description && (
              <p className="text-xs text-slate-500 truncate max-w-[300px]">
                {item.description}
              </p>
            )}
          </div>
        </div>
      ),
    },
    {
      key: "pages_count",
      header: "Pages",
      render: (item) => (
        <div className="flex items-center gap-2">
          <Store className="w-4 h-4 text-slate-500" />
          <span className="font-semibold text-slate-200">
            {item.pages_count}
          </span>
        </div>
      ),
      className: "w-24",
    },
    {
      key: "status",
      header: "Status",
      render: (item) => (
        <Badge
          variant={item.is_active ? "success" : "default"}
          size="sm"
        >
          {item.is_active ? "Active" : "Inactive"}
        </Badge>
      ),
      className: "w-24",
    },
    {
      key: "created_at",
      header: "Created",
      render: (item) => (
        <span className="text-sm text-slate-400">
          {new Date(item.created_at).toLocaleDateString()}
        </span>
      ),
      className: "w-32",
    },
    {
      key: "actions",
      header: "",
      render: (item) => (
        <Link
          href={`/watchlists/${encodeURIComponent(item.id)}`}
          className="flex items-center gap-1 text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors"
        >
          View
          <ChevronRight className="w-4 h-4" />
        </Link>
      ),
      className: "w-24",
    },
  ];

  if (error) {
    return (
      <>
        <Header title="Watchlists" subtitle="Track and monitor shops" />
        <PageContent>
          <ErrorState
            title="Failed to load watchlists"
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
        title="Watchlists"
        subtitle={`${watchlists.length} watchlists`}
        actions={
          <div className="flex items-center gap-2">
            <RefreshButton onClick={fetchData} isLoading={isLoading} />
            <Button
              variant="primary"
              size="md"
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Watchlist
            </Button>
          </div>
        }
      />
      <PageContent>
        {isLoading ? (
          <LoadingState message="Loading watchlists..." />
        ) : watchlists.length === 0 ? (
          <Card>
            <CardBody>
              <div className="py-12 text-center">
                <ListChecks className="w-12 h-12 mx-auto mb-4 text-slate-500 opacity-50" />
                <h3 className="text-lg font-medium text-slate-200 mb-2">
                  No watchlists yet
                </h3>
                <p className="text-slate-400 mb-4">
                  Create your first watchlist to start tracking shops
                </p>
                <Button
                  variant="primary"
                  onClick={() => setShowCreateModal(true)}
                  className="inline-flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Create Watchlist
                </Button>
              </div>
            </CardBody>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <ListChecks className="w-5 h-5 text-blue-400" />
                Your Watchlists
              </div>
            </CardHeader>
            <CardBody className="p-0">
              <Table
                columns={columns}
                data={watchlists}
                keyExtractor={(item) => item.id}
                emptyMessage="No watchlists found"
              />
            </CardBody>
          </Card>
        )}

        {/* Create Watchlist Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
            <div className="bg-slate-900 rounded-xl border border-slate-700 p-6 w-full max-w-md shadow-xl">
              <h2 className="text-xl font-semibold text-slate-100 mb-4">
                Create New Watchlist
              </h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={newWatchlistName}
                    onChange={(e) => setNewWatchlistName(e.target.value)}
                    placeholder="e.g., Top FR Winners"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">
                    Description
                  </label>
                  <textarea
                    value={newWatchlistDescription}
                    onChange={(e) => setNewWatchlistDescription(e.target.value)}
                    placeholder="Optional description..."
                    rows={3}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewWatchlistName("");
                    setNewWatchlistDescription("");
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleCreateWatchlist}
                  disabled={!newWatchlistName.trim() || isCreating}
                >
                  {isCreating ? "Creating..." : "Create"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </PageContent>
    </>
  );
}
