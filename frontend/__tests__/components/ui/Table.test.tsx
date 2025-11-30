import { render, screen, fireEvent } from "@testing-library/react";
import { Table, Pagination, type Column } from "@/components/ui/Table";

interface TestItem {
  id: string;
  name: string;
  value: number;
}

const testData: TestItem[] = [
  { id: "1", name: "Item 1", value: 100 },
  { id: "2", name: "Item 2", value: 200 },
  { id: "3", name: "Item 3", value: 300 },
];

const testColumns: Column<TestItem>[] = [
  {
    key: "name",
    header: "Name",
    render: (item) => item.name,
  },
  {
    key: "value",
    header: "Value",
    render: (item) => item.value.toString(),
  },
];

describe("Table", () => {
  it("renders headers correctly", () => {
    render(
      <Table
        columns={testColumns}
        data={testData}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Value")).toBeInTheDocument();
  });

  it("renders data rows correctly", () => {
    render(
      <Table
        columns={testColumns}
        data={testData}
        keyExtractor={(item) => item.id}
      />
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
    expect(screen.getByText("300")).toBeInTheDocument();
  });

  it("shows empty message when data is empty", () => {
    render(
      <Table
        columns={testColumns}
        data={[]}
        keyExtractor={(item) => item.id}
        emptyMessage="No items found"
      />
    );

    expect(screen.getByText("No items found")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(
      <Table
        columns={testColumns}
        data={[]}
        keyExtractor={(item) => item.id}
        isLoading={true}
      />
    );

    // Should show loading skeletons (animated divs)
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("calls onRowClick when row is clicked", () => {
    const handleRowClick = jest.fn();

    render(
      <Table
        columns={testColumns}
        data={testData}
        keyExtractor={(item) => item.id}
        onRowClick={handleRowClick}
      />
    );

    fireEvent.click(screen.getByText("Item 1"));
    expect(handleRowClick).toHaveBeenCalledWith(testData[0]);
  });

  it("applies custom className to table", () => {
    render(
      <Table
        columns={testColumns}
        data={testData}
        keyExtractor={(item) => item.id}
        className="custom-table"
      />
    );

    const table = document.querySelector("table");
    expect(table).toHaveClass("custom-table");
  });

  it("applies column className to cells", () => {
    const columnsWithClassName: Column<TestItem>[] = [
      {
        key: "name",
        header: "Name",
        render: (item) => <span data-testid="name-cell">{item.name}</span>,
        className: "name-column",
      },
    ];

    render(
      <Table
        columns={columnsWithClassName}
        data={testData}
        keyExtractor={(item) => item.id}
      />
    );

    const cells = screen.getAllByTestId("name-cell");
    cells.forEach((cell) => {
      expect(cell.closest("td")).toHaveClass("name-column");
    });
  });
});

describe("Pagination", () => {
  it("renders page buttons", () => {
    render(
      <Pagination currentPage={1} totalPages={5} onPageChange={jest.fn()} />
    );

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("calls onPageChange when page is clicked", () => {
    const handlePageChange = jest.fn();

    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={handlePageChange}
      />
    );

    fireEvent.click(screen.getByText("3"));
    expect(handlePageChange).toHaveBeenCalledWith(3);
  });

  it("disables Previous button on first page", () => {
    render(
      <Pagination currentPage={1} totalPages={5} onPageChange={jest.fn()} />
    );

    expect(screen.getByText("Previous")).toBeDisabled();
  });

  it("disables Next button on last page", () => {
    render(
      <Pagination currentPage={5} totalPages={5} onPageChange={jest.fn()} />
    );

    expect(screen.getByText("Next")).toBeDisabled();
  });

  it("does not render when totalPages is 1", () => {
    const { container } = render(
      <Pagination currentPage={1} totalPages={1} onPageChange={jest.fn()} />
    );

    expect(container.firstChild).toBeNull();
  });

  it("handles Previous button click", () => {
    const handlePageChange = jest.fn();

    render(
      <Pagination
        currentPage={3}
        totalPages={5}
        onPageChange={handlePageChange}
      />
    );

    fireEvent.click(screen.getByText("Previous"));
    expect(handlePageChange).toHaveBeenCalledWith(2);
  });

  it("handles Next button click", () => {
    const handlePageChange = jest.fn();

    render(
      <Pagination
        currentPage={3}
        totalPages={5}
        onPageChange={handlePageChange}
      />
    );

    fireEvent.click(screen.getByText("Next"));
    expect(handlePageChange).toHaveBeenCalledWith(4);
  });

  it("shows ellipsis for many pages", () => {
    render(
      <Pagination currentPage={5} totalPages={10} onPageChange={jest.fn()} />
    );

    // Should show ellipsis
    const ellipsis = screen.getAllByText("...");
    expect(ellipsis.length).toBeGreaterThan(0);
  });

  it("highlights current page", () => {
    render(
      <Pagination currentPage={3} totalPages={5} onPageChange={jest.fn()} />
    );

    const currentPageButton = screen.getByText("3");
    expect(currentPageButton).toHaveClass("bg-blue-600");
  });
});
