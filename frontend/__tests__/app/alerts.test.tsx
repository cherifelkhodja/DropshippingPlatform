import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import AlertsPage from "@/app/alerts/page";
import * as api from "@/lib/api";

// Mock the API module
jest.mock("@/lib/api");

const mockAlerts = {
  items: [
    {
      id: "alert-1",
      page_id: "page-1",
      alert_type: "SCORE_JUMP",
      severity: "warning",
      message: "Score jumped from 45.0 to 72.0 (+27.0)",
      old_score: 45.0,
      new_score: 72.0,
      old_tier: null,
      new_tier: null,
      created_at: "2024-03-20T15:45:00Z",
    },
    {
      id: "alert-2",
      page_id: "page-2",
      alert_type: "TIER_UP",
      severity: "info",
      message: "Tier upgraded from M to L",
      old_score: null,
      new_score: null,
      old_tier: "M",
      new_tier: "L",
      created_at: "2024-03-20T14:30:00Z",
    },
    {
      id: "alert-3",
      page_id: "page-1",
      alert_type: "NEW_ADS_BOOST",
      severity: "info",
      message: "New ads boost detected: 15 new ads",
      old_score: null,
      new_score: null,
      old_tier: null,
      new_tier: null,
      created_at: "2024-03-19T10:00:00Z",
    },
  ],
  count: 3,
};

describe("AlertsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.getRecentAlerts as jest.Mock).mockResolvedValue(mockAlerts);
  });

  it("renders alerts page with title", async () => {
    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByText("Alerts")).toBeInTheDocument();
    });
  });

  it("displays loading state initially", () => {
    render(<AlertsPage />);
    expect(screen.getByText("Loading alerts...")).toBeInTheDocument();
  });

  it("displays alerts after loading", async () => {
    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Score jumped from 45.0 to 72.0/)).toBeInTheDocument();
      expect(screen.getByText(/Tier upgraded from M to L/)).toBeInTheDocument();
    });
  });

  it("shows severity badges", async () => {
    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("warning").length).toBeGreaterThan(0);
      expect(screen.getAllByText("info").length).toBeGreaterThan(0);
    });
  });

  it("allows filtering by alert type", async () => {
    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("Alert Type")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Alert Type"), {
      target: { value: "SCORE_JUMP" },
    });

    // After filter, only SCORE_JUMP alerts should show
    await waitFor(() => {
      expect(screen.getByText(/Score jumped from 45.0 to 72.0/)).toBeInTheDocument();
      expect(screen.queryByText(/Tier upgraded from M to L/)).not.toBeInTheDocument();
    });
  });

  it("allows filtering by severity", async () => {
    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("Severity")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Severity"), {
      target: { value: "warning" },
    });

    // After filter, only warning severity alerts should show
    await waitFor(() => {
      expect(screen.getByText(/Score jumped from 45.0 to 72.0/)).toBeInTheDocument();
    });
  });

  it("displays empty state when no alerts", async () => {
    (api.getRecentAlerts as jest.Mock).mockResolvedValue({ items: [], count: 0 });

    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByText("No alerts yet")).toBeInTheDocument();
    });
  });

  it("displays error state on API failure", async () => {
    (api.getRecentAlerts as jest.Mock).mockRejectedValue(new Error("API Error"));

    render(<AlertsPage />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load alerts")).toBeInTheDocument();
    });
  });

  it("groups alerts by date", async () => {
    render(<AlertsPage />);

    await waitFor(() => {
      // Check that dates are displayed
      expect(screen.getByText(/3\/20\/2024/)).toBeInTheDocument();
    });
  });
});
