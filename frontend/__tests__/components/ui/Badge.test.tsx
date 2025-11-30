import { render, screen } from "@testing-library/react";
import { TierBadge, MatchBadge, StatusBadge, Badge } from "@/components/ui/Badge";

describe("TierBadge", () => {
  it("renders XXL tier with correct text", () => {
    render(<TierBadge tier="XXL" />);
    expect(screen.getByText("XXL")).toBeInTheDocument();
  });

  it("renders XL tier with correct text", () => {
    render(<TierBadge tier="XL" />);
    expect(screen.getByText("XL")).toBeInTheDocument();
  });

  it("renders L tier with correct text", () => {
    render(<TierBadge tier="L" />);
    expect(screen.getByText("L")).toBeInTheDocument();
  });

  it("renders M tier with correct text", () => {
    render(<TierBadge tier="M" />);
    expect(screen.getByText("M")).toBeInTheDocument();
  });

  it("renders S tier with correct text", () => {
    render(<TierBadge tier="S" />);
    expect(screen.getByText("S")).toBeInTheDocument();
  });

  it("renders XS tier with correct text", () => {
    render(<TierBadge tier="XS" />);
    expect(screen.getByText("XS")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<TierBadge tier="XXL" className="custom-class" />);
    expect(screen.getByText("XXL")).toHaveClass("custom-class");
  });

  it("renders with different sizes", () => {
    const { rerender } = render(<TierBadge tier="XXL" size="sm" />);
    expect(screen.getByText("XXL")).toBeInTheDocument();

    rerender(<TierBadge tier="XXL" size="md" />);
    expect(screen.getByText("XXL")).toBeInTheDocument();

    rerender(<TierBadge tier="XXL" size="lg" />);
    expect(screen.getByText("XXL")).toBeInTheDocument();
  });
});

describe("MatchBadge", () => {
  it("renders strong match with correct text", () => {
    render(<MatchBadge strength="strong" />);
    expect(screen.getByText("Strong")).toBeInTheDocument();
  });

  it("renders medium match with correct text", () => {
    render(<MatchBadge strength="medium" />);
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  it("renders weak match with correct text", () => {
    render(<MatchBadge strength="weak" />);
    expect(screen.getByText("Weak")).toBeInTheDocument();
  });

  it("renders none match with correct text", () => {
    render(<MatchBadge strength="none" />);
    expect(screen.getByText("None")).toBeInTheDocument();
  });
});

describe("StatusBadge", () => {
  it("renders active status", () => {
    render(<StatusBadge status="active" />);
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("renders with custom label", () => {
    render(<StatusBadge status="active" label="Online" />);
    expect(screen.getByText("Online")).toBeInTheDocument();
  });

  it("renders inactive status", () => {
    render(<StatusBadge status="inactive" />);
    expect(screen.getByText("inactive")).toBeInTheDocument();
  });
});

describe("Badge", () => {
  it("renders children correctly", () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText("Test Badge")).toBeInTheDocument();
  });

  it("applies variant styles", () => {
    const { rerender } = render(<Badge variant="success">Success</Badge>);
    expect(screen.getByText("Success")).toBeInTheDocument();

    rerender(<Badge variant="warning">Warning</Badge>);
    expect(screen.getByText("Warning")).toBeInTheDocument();

    rerender(<Badge variant="error">Error</Badge>);
    expect(screen.getByText("Error")).toBeInTheDocument();

    rerender(<Badge variant="info">Info</Badge>);
    expect(screen.getByText("Info")).toBeInTheDocument();
  });
});
