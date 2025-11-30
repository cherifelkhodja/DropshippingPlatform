import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import WatchlistsPage from "@/app/watchlists/page";
import * as api from "@/lib/api";

// Mock the API module
jest.mock("@/lib/api");

const mockWatchlists = {
  items: [
    {
      id: "watchlist-1",
      name: "Top FR Winners",
      description: "French stores with high scores",
      created_at: "2024-03-20T15:45:00Z",
      is_active: true,
      pages_count: 10,
    },
    {
      id: "watchlist-2",
      name: "US Competitors",
      description: null,
      created_at: "2024-03-19T10:00:00Z",
      is_active: true,
      pages_count: 5,
    },
  ],
  count: 2,
};

describe("WatchlistsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getWatchlists as jest.Mock).mockResolvedValue(mockWatchlists);
  });

  it("renders watchlists page with title", async () => {
    render(<WatchlistsPage />);

    await waitFor(() => {
      expect(screen.getByText("Watchlists")).toBeInTheDocument();
    });
  });

  it("displays loading state initially", () => {
    render(<WatchlistsPage />);
    expect(screen.getByText("Loading watchlists...")).toBeInTheDocument();
  });

  it("displays watchlists after loading", async () => {
    render(<WatchlistsPage />);

    await waitFor(() => {
      expect(screen.getByText("Top FR Winners")).toBeInTheDocument();
      expect(screen.getByText("US Competitors")).toBeInTheDocument();
    });
  });

  it("shows pages count for each watchlist", async () => {
    render(<WatchlistsPage />);

    await waitFor(() => {
      expect(screen.getByText("10")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
    });
  });

  it("shows create watchlist button", async () => {
    render(<WatchlistsPage />);

    await waitFor(() => {
      expect(screen.getByText("New Watchlist")).toBeInTheDocument();
    });
  });

  it("opens create modal when clicking new watchlist button", async () => {
    render(<WatchlistsPage />);

    await waitFor(() => {
      expect(screen.getByText("New Watchlist")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("New Watchlist"));

    expect(screen.getByText("Create New Watchlist")).toBeInTheDocument();
  });

  it("displays empty state when no watchlists", async () => {
    (api.getWatchlists as jest.Mock).mockResolvedValue({ items: [], count: 0 });

    render(<WatchlistsPage />);

    await waitFor(() => {
      expect(screen.getByText("No watchlists yet")).toBeInTheDocument();
    });
  });

  it("displays error state on API failure", async () => {
    (api.getWatchlists as jest.Mock).mockRejectedValue(new Error("API Error"));

    render(<WatchlistsPage />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load watchlists")).toBeInTheDocument();
    });
  });
});
