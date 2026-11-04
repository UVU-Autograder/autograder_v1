import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import AssignmentsClient from "../assignments-client";
import { apiClient } from "@/lib/api-client";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("assignment catalogs", () => {
  it("lists sandbox-disabled assignments for teachers using the staff API and its point totals", async () => {
    const get = vi.spyOn(apiClient, "get").mockImplementation(async (path) => ({
      course_id: "cs1410",
      assignments: path.startsWith("/staff/") ? [{
        id: "draft", course_id: "cs1410", title: "Draft assignment", language: "python",
        sandbox_enabled: false, base_points: 25, extra_credit_points: 5,
      }] : [],
    }));
    render(<AssignmentsClient courseId="cs1410" mode="staff" />);
    await screen.findByText("Draft assignment");
    expect(get).toHaveBeenCalledWith("/staff/courses/cs1410/assignments");
    expect(screen.getByText("25 pts")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Draft assignment/ }).getAttribute("href"))
      .toBe("/staff/courses/cs1410/assignments/draft");
  });

  it("keeps student assignment discovery on the sandbox API", async () => {
    const get = vi.spyOn(apiClient, "get").mockResolvedValue({ course_id: "cs1410", assignments: [] });
    render(<AssignmentsClient courseId="cs1410" mode="sandbox" />);
    await screen.findByText("No assignments available yet.");
    expect(get).toHaveBeenCalledWith("/sandbox/courses/cs1410/assignments");
    expect(screen.queryByRole("link", { name: "New Assignment" })).toBeNull();
  });
});
