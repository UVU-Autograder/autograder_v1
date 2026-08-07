import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import VisualDiffViewer from "../visual-diff-viewer";

describe("VisualDiffViewer Component", () => {
  it("renders expected and student output header labels", () => {
    render(<VisualDiffViewer expected="hello" actual="hello" />);
    expect(screen.getByText("Output Difference")).toBeDefined();
    expect(screen.getByText("Expected")).toBeDefined();
    expect(screen.getByText("Student")).toBeDefined();
  });

  it("renders diff lines when expected and actual outputs differ", () => {
    render(
      <VisualDiffViewer
        expected={`Line 1
Line 2`}
        actual={`Line 1
Line 3`}
      />
    );
    expect(screen.getByText("- Line 2")).toBeDefined();
    expect(screen.getByText("+ Line 3")).toBeDefined();
  });
});
