import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { CourseSectionsDialog } from "../course-sections-dialog";
import * as coursesApi from "@/features/courses/api";
import { CourseAdminDetail } from "@/features/courses/types";

vi.mock("@/features/courses/api", () => ({
  getCourseSections: vi.fn(),
  createAdminSection: vi.fn(),
  updateAdminSection: vi.fn(),
  deleteAdminSection: vi.fn(),
}));

const mockCourse: CourseAdminDetail = {
  id: 42,
  code: "cs1400",
  title: "Intro to Python",
  term: "Fall 2026",
  is_active: true,
  default_concepts: ["loops"],
  section_count: 2,
  assignment_count: 5,
  instructor_id: null,
  instructor_email: "instructor@uvu.edu",
  ia_id: null,
  ia_email: null,
};

describe("CourseSectionsDialog Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches and renders existing course sections", async () => {
    vi.mocked(coursesApi.getCourseSections).mockResolvedValueOnce([
      { id: 101, course_id: 42, crn: "12345", is_active: true },
      { id: 102, course_id: 42, crn: "67890", is_active: false },
    ]);

    render(
      <CourseSectionsDialog
        isOpen={true}
        onOpenChange={vi.fn()}
        course={mockCourse}
      />,
    );

    expect(screen.getByText(/Manage Sections — CS1400/i)).toBeDefined();
    await waitFor(() => {
      expect(screen.getByText(/CRN: 12345/i)).toBeDefined();
      expect(screen.getByText(/CRN: 67890/i)).toBeDefined();
      expect(screen.getByText("Active")).toBeDefined();
      expect(screen.getByText("Inactive")).toBeDefined();
    });
  });

  it("submits a new section CRN", async () => {
    vi.mocked(coursesApi.getCourseSections).mockResolvedValue([]);
    vi.mocked(coursesApi.createAdminSection).mockResolvedValueOnce({
      id: 103,
      course_id: 42,
      crn: "99999",
      is_active: true,
    });

    render(
      <CourseSectionsDialog
        isOpen={true}
        onOpenChange={vi.fn()}
        course={mockCourse}
      />,
    );

    const input = screen.getByLabelText("Section CRN");
    fireEvent.change(input, { target: { value: "99999" } });

    const addBtn = screen.getByRole("button", { name: /Add Section/i });
    fireEvent.click(addBtn);

    await waitFor(() => {
      expect(coursesApi.createAdminSection).toHaveBeenCalledWith(42, {
        crn: "99999",
      });
    });
  });

  it("toggles section active state", async () => {
    vi.mocked(coursesApi.getCourseSections).mockResolvedValue([
      { id: 101, course_id: 42, crn: "12345", is_active: true },
      { id: 102, course_id: 42, crn: "67890", is_active: false },
    ]);
    vi.mocked(coursesApi.deleteAdminSection).mockResolvedValueOnce(undefined);
    vi.mocked(coursesApi.updateAdminSection).mockResolvedValueOnce({
      id: 102,
      course_id: 42,
      crn: "67890",
      is_active: true,
    });

    render(
      <CourseSectionsDialog
        isOpen={true}
        onOpenChange={vi.fn()}
        course={mockCourse}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText(/CRN: 12345/i)).toBeDefined();
      expect(screen.getByText(/CRN: 67890/i)).toBeDefined();
    });

    const deactivateBtn = screen.getByRole("button", { name: /^Deactivate$/i });
    fireEvent.click(deactivateBtn);
    expect(coursesApi.deleteAdminSection).toHaveBeenCalledWith(101);

    const activateBtn = screen.getByRole("button", { name: /^Activate$/i });
    fireEvent.click(activateBtn);
    expect(coursesApi.updateAdminSection).toHaveBeenCalledWith(102, {
      is_active: true,
    });
  });
});
