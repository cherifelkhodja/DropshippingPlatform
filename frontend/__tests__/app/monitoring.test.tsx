import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import MonitoringPage from "@/app/monitoring/page";
import * as api from "@/lib/api";

// Mock the API module
jest.mock("@/lib/api");

const mockSummary = {
  total_pages: 1250,
  pages_with_scores: 1100,
  alerts_last_24h: 45,
  alerts_last_7d: 312,
  last_metrics_snapshot_date: "2024-03-20",
  metrics_snapshots_count: 3650,
  generated_at: "2024-03-20T15:45:00Z",
};

const mockKeywords = {
  items: [
    {
      keyword: "dropshipping supplies",
      country: "US",
      created_at: "2024-03-20T10:30:00Z",
      total_ads_found: 150,
      total_pages_found: 45,
      scan_id: "scan-1",
    },
    {
      keyword: "pet products",
      country: "FR",
      created_at: "2024-03-20T09:00:00Z",
      total_ads_found: 80,
      total_pages_found: 25,
      scan_id: "scan-2",
    },
  ],
  total: 2,
};

const mockScans = {
  items: [
    {
      id: "scan-1",
      status: "completed",
      started_at: "2024-03-20T10:30:00Z",
      completed_at: "2024-03-20T10:32:15Z",
      page_id: "page-1",
      result_summary: "ads=25, products=150, shopify=true",
    },
    {
      id: "scan-2",
      status: "running",
      started_at: "2024-03-20T10:35:00Z",
      completed_at: null,
      page_id: "page-2",
      result_summary: null,
    },
  ],
  total: 2,
  offset: 0,
  limit: 20,
};

describe("MonitoringPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getMonitoringSummary as jest.Mock).mockResolvedValue(mockSummary);
    (api.getAdminKeywords as jest.Mock).mockResolvedValue(mockKeywords);
    (api.getAdminScans as jest.Mock).mockResolvedValue(mockScans);
    (api.triggerDailySnapshot as jest.Mock).mockResolvedValue({
      status: "dispatched",
      task_id: "task-123",
      snapshot_date: "2024-03-20",
    });
  });

  it("renders monitoring page with title", async () => {
    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("Monitoring")).toBeInTheDocument();
    });
  });

  it("displays loading state initially", () => {
    render(<MonitoringPage />);
    expect(screen.getByText("Loading monitoring data...")).toBeInTheDocument();
  });

  it("displays summary statistics after loading", async () => {
    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("1250")).toBeInTheDocument(); // Total pages
      expect(screen.getByText("1100")).toBeInTheDocument(); // Pages with scores
      expect(screen.getByText("45")).toBeInTheDocument(); // Alerts 24h
      expect(screen.getByText("312")).toBeInTheDocument(); // Alerts 7d
    });
  });

  it("displays recent keyword runs", async () => {
    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("dropshipping supplies")).toBeInTheDocument();
      expect(screen.getByText("pet products")).toBeInTheDocument();
    });
  });

  it("displays recent scans", async () => {
    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("completed")).toBeInTheDocument();
      expect(screen.getByText("running")).toBeInTheDocument();
    });
  });

  it("has trigger snapshot button", async () => {
    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("Trigger Snapshot")).toBeInTheDocument();
    });
  });

  it("triggers snapshot when button is clicked", async () => {
    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("Trigger Snapshot")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Trigger Snapshot"));

    await waitFor(() => {
      expect(api.triggerDailySnapshot).toHaveBeenCalled();
      expect(screen.getByText(/Snapshot triggered/)).toBeInTheDocument();
    });
  });

  it("displays system status section", async () => {
    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("System Status")).toBeInTheDocument();
      expect(screen.getByText("Last Metrics Snapshot")).toBeInTheDocument();
    });
  });

  it("displays error state on API failure", async () => {
    (api.getMonitoringSummary as jest.Mock).mockRejectedValue(new Error("API Error"));

    render(<MonitoringPage />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load monitoring data")).toBeInTheDocument();
    });
  });
});
