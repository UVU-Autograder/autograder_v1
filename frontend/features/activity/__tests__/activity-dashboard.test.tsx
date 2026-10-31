import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ActivityMetricCards } from "../components/activity-metric-cards";
import { ActivityVelocityChart } from "../components/activity-velocity-chart";
import { AttemptDistributionCard } from "../components/attempt-distribution-card";
import { ErrorBottlenecksCard } from "../components/error-bottlenecks-card";
import { AssignmentActivityTable } from "../components/assignment-activity-table";
import { getAdminActivity, getCourseActivity } from "../api";
import { MOCK_SYSTEM_ACTIVITY } from "@/lib/mock-data";

describe("Activity Metric Cards", () => {
  it("renders key student practice metrics correctly", () => {
    render(
      <ActivityMetricCards
        totalRuns={142}
        activeStudents={38}
        passRate={76.8}
        totalAiTokens={28450}
        totalAiRequests={64}
      />
    );

    expect(screen.getByText("38")).toBeDefined();
    expect(screen.getByText("142")).toBeDefined();
    expect(screen.getByText("76.8%")).toBeDefined();
    expect(screen.getByText("64")).toBeDefined();
    expect(screen.getByText("Avg 3.7 runs / student")).toBeDefined();
    expect(screen.getByText("28,450 tokens served")).toBeDefined();
  });
});

describe("Activity Velocity Chart", () => {
  it("renders velocity chart bars and legend", () => {
    render(<ActivityVelocityChart velocity={MOCK_SYSTEM_ACTIVITY.velocity} />);

    expect(screen.getByText("Submission Velocity")).toBeDefined();
    expect(screen.getByText("Passed")).toBeDefined();
    expect(screen.getByText("Failed")).toBeDefined();
  });

  it("renders fallback message when velocity is empty", () => {
    render(<ActivityVelocityChart velocity={[]} />);

    expect(screen.getByText("No sandbox submissions in this time window.")).toBeDefined();
  });
});

describe("Attempt Distribution Card", () => {
  it("renders distribution histogram buckets and counts", () => {
    render(<AttemptDistributionCard distribution={MOCK_SYSTEM_ACTIVITY.attempt_distribution} />);

    expect(screen.getByText("Attempt Distribution")).toBeDefined();
    expect(screen.getByText("1 attempt")).toBeDefined();
    expect(screen.getByText("2-3 attempts")).toBeDefined();
    expect(screen.getByText("6 students (15.8%)")).toBeDefined();
    expect(screen.getByText("14 students (36.8%)")).toBeDefined();
  });
});

describe("Error Bottlenecks Card", () => {
  it("renders ranked bottlenecks with badges", () => {
    render(<ErrorBottlenecksCard bottlenecks={MOCK_SYSTEM_ACTIVITY.top_bottlenecks} />);

    expect(screen.getByText("Failure Bottlenecks")).toBeDefined();
    expect(screen.getByText("ag_calculate_cost")).toBeDefined();
    expect(screen.getByText("SyntaxError")).toBeDefined();
    expect(screen.getByText("forbid_sorting")).toBeDefined();
  });

  it("renders fallback message when bottlenecks list is empty", () => {
    render(<ErrorBottlenecksCard bottlenecks={[]} />);

    expect(screen.getByText("No recurring error bottlenecks detected in this window.")).toBeDefined();
  });
});

describe("Assignment Activity Table", () => {
  it("renders assignment rows and pass rates", () => {
    render(<AssignmentActivityTable assignments={MOCK_SYSTEM_ACTIVITY.assignments} courseCode="cs1410" />);

    expect(screen.getByText("Image Processing")).toBeDefined();
    expect(screen.getByText("(lab1)")).toBeDefined();
    expect(screen.getByText("Packaging Tracker")).toBeDefined();
    expect(screen.getByText("(ds1)")).toBeDefined();
    expect(screen.getByText("81.8%")).toBeDefined();
    expect(screen.getByText("68.5%")).toBeDefined();
  });
});

describe("Activity API Client & Mock Handlers", () => {
  it("fetches admin activity via mock interceptor in dev mode", async () => {
    const data = await getAdminActivity(168);
    expect(data.total_sandbox_runs).toBe(142);
    expect(data.active_student_sessions).toBe(38);
    expect(data.velocity.length).toBeGreaterThan(0);
    expect(data.assignments.length).toBeGreaterThan(0);
  });

  it("fetches course-scoped activity via mock interceptor in dev mode", async () => {
    const data = await getCourseActivity("cs1410", 168);
    expect(data.course_code).toBe("cs1410");
    expect(data.total_sandbox_runs).toBe(142);
    expect(data.assignments.length).toBeGreaterThan(0);
  });
});
