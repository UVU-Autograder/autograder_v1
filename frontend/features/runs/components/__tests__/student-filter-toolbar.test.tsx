import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import React from "react";
import { StudentFilterToolbar } from "../student-filter-toolbar";

describe("StudentFilterToolbar Component", () => {
  const counts = { all: 15, ungraded: 3, graded: 12, failed: 2 };

  it("renders search input and filter buttons with counts", () => {
    render(
      <StudentFilterToolbar
        searchQuery=""
        onSearchChange={vi.fn()}
        statusFilter="all"
        onStatusFilterChange={vi.fn()}
        counts={counts}
      />,
    );

    expect(
      screen.getByPlaceholderText(/Search by student name or Canvas ID/i),
    ).toBeDefined();
    expect(screen.getByText("All (15)")).toBeDefined();
    expect(screen.getByText("Needs Grading (3)")).toBeDefined();
    expect(screen.getByText("Graded (12)")).toBeDefined();
    expect(screen.getByText("Failed (2)")).toBeDefined();
  });

  it("triggers onSearchChange when user types in search box", () => {
    const handleSearchChange = vi.fn();
    render(
      <StudentFilterToolbar
        searchQuery=""
        onSearchChange={handleSearchChange}
        statusFilter="all"
        onStatusFilterChange={vi.fn()}
        counts={counts}
      />,
    );

    const input = screen.getByTestId("student-search-input");
    fireEvent.change(input, { target: { value: "smith" } });
    expect(handleSearchChange).toHaveBeenCalledWith("smith");
  });

  it("triggers onStatusFilterChange when clicking filter buttons", () => {
    const handleFilterChange = vi.fn();
    render(
      <StudentFilterToolbar
        searchQuery=""
        onSearchChange={vi.fn()}
        statusFilter="all"
        onStatusFilterChange={handleFilterChange}
        counts={counts}
      />,
    );

    fireEvent.click(screen.getByTestId("filter-ungraded"));
    expect(handleFilterChange).toHaveBeenCalledWith("ungraded");

    fireEvent.click(screen.getByTestId("filter-failed"));
    expect(handleFilterChange).toHaveBeenCalledWith("failed");
  });
});
