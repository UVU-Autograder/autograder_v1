import { render, screen } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { StaffAuthGuard } from "../staff-auth-guard";
import { getOppositePath } from "../navbar";

const mockReplace = vi.fn();
const mockPush = vi.fn();
let mockCurrentPath = "/staff/courses";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: mockPush,
  }),
  usePathname: () => mockCurrentPath,
}));

describe("StaffAuthGuard Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCurrentPath = "/staff/courses";
    localStorage.clear();
    sessionStorage.clear();
  });

  it("redirects unauthenticated visitor using router.replace with return_to to avoid trapping browser history", () => {
    render(
      <StaffAuthGuard>
        <div>Protected Staff Content</div>
      </StaffAuthGuard>
    );

    expect(mockReplace).toHaveBeenCalledWith("/staff/login?return_to=%2Fstaff%2Fcourses");
    expect(mockPush).not.toHaveBeenCalled();
    expect(screen.getByText("Checking authorization...")).toBeDefined();
  });

  it("preserves deep link path in return_to query parameter when redirecting unauthenticated staff", () => {
    mockCurrentPath = "/staff/courses/cs3450/assignments/lab1";
    render(
      <StaffAuthGuard>
        <div>Protected Staff Content</div>
      </StaffAuthGuard>
    );

    expect(mockReplace).toHaveBeenCalledWith(
      "/staff/login?return_to=%2Fstaff%2Fcourses%2Fcs3450%2Fassignments%2Flab1"
    );
  });

  it("renders protected content when staff token exists", () => {
    localStorage.setItem("token", "mock-valid-token");
    render(
      <StaffAuthGuard>
        <div>Protected Staff Content</div>
      </StaffAuthGuard>
    );

    expect(mockReplace).not.toHaveBeenCalled();
    expect(screen.getByText("Protected Staff Content")).toBeDefined();
  });
});

describe("getOppositePath URL mapping", () => {
  it("maps staff admin, login, and courses roots to /sandbox", () => {
    expect(getOppositePath("/staff/admin")).toBe("/sandbox");
    expect(getOppositePath("/staff/admin/users")).toBe("/sandbox");
    expect(getOppositePath("/staff/login")).toBe("/sandbox");
    expect(getOppositePath("/staff/courses")).toBe("/sandbox");
    expect(getOppositePath("/staff/courses/")).toBe("/sandbox");
  });

  it("maps staff new assignment and course settings to course sandbox assignments", () => {
    expect(getOppositePath("/staff/courses/cs3450/assignments/new")).toBe(
      "/sandbox/cs3450/assignments"
    );
    expect(getOppositePath("/staff/courses/cs3450/settings")).toBe(
      "/sandbox/cs3450/assignments"
    );
  });

  it("maps staff assignment deep links and nested subpaths to sandbox assignment view", () => {
    expect(getOppositePath("/staff/courses/cs3450/assignments/lab1")).toBe(
      "/sandbox/cs3450/assignments/lab1"
    );
    expect(getOppositePath("/staff/courses/cs3450/assignments/lab1/runs")).toBe(
      "/sandbox/cs3450/assignments/lab1"
    );
  });

  it("maps sandbox assignment to staff assignment", () => {
    expect(getOppositePath("/sandbox/cs3450/assignments/lab1")).toBe(
      "/staff/courses/cs3450/assignments/lab1"
    );
  });

  it("maps sandbox root and courses to staff counterparts", () => {
    expect(getOppositePath("/sandbox")).toBe("/staff/courses");
    expect(getOppositePath("/sandbox/")).toBe("/staff/courses");
    expect(getOppositePath("/sandbox/cs3450")).toBe("/staff/courses/cs3450/assignments");
  });

  it("returns null for non-staff non-sandbox paths", () => {
    expect(getOppositePath("/")).toBeNull();
    expect(getOppositePath("/about")).toBeNull();
  });
});
