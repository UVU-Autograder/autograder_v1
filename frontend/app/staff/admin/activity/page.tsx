"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCwIcon } from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageLoading } from "@/components/page-status";
import { Button } from "@/components/ui/button";
import { getAdminActivity } from "@/features/activity/api";
import type { SystemActivityResponse } from "@/features/activity/types";
import { ActivityMetricCards } from "@/features/activity/components/activity-metric-cards";
import { ActivityVelocityChart } from "@/features/activity/components/activity-velocity-chart";
import { AttemptDistributionCard } from "@/features/activity/components/attempt-distribution-card";
import { ErrorBottlenecksCard } from "@/features/activity/components/error-bottlenecks-card";
import { AssignmentActivityTable } from "@/features/activity/components/assignment-activity-table";

export default function AdminActivityPage() {
  const [activity, setActivity] = useState<SystemActivityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [windowHours, setWindowHours] = useState<number>(168);

  const fetchActivity = useCallback(async (hours = windowHours) => {
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await getAdminActivity(hours);
      setActivity(data);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to load activity telemetry.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [windowHours]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setError(null);
      try {
        const data = await getAdminActivity(windowHours);
        if (!cancelled) setActivity(data);
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          setError(err instanceof Error ? err.message : "Failed to load activity telemetry.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
          setIsRefreshing(false);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [windowHours]);

  if (isLoading) {
    return <PageLoading className="h-screen">Loading student activity telemetry...</PageLoading>;
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pt-8 pb-16 space-y-6">
      <Breadcrumbs
        items={[
          { label: "Courses", href: "/staff/courses" },
          { label: "Admin", href: "/staff/admin" },
          { label: "Activity Monitor" },
        ]}
      />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
        <AdminPageHeader
          title="Student Activity Monitor"
          description="System-wide student practice volume, submission velocity, attempt distributions, and error bottlenecks"
        />

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {/* Time window toggles */}
          <div className="flex items-center rounded-lg border border-border p-0.5 text-xs">
            <button
              onClick={() => setWindowHours(24)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                windowHours === 24
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              24h
            </button>
            <button
              onClick={() => setWindowHours(168)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                windowHours === 168
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              7d
            </button>
            <button
              onClick={() => setWindowHours(720)}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                windowHours === 720
                  ? "bg-primary text-primary-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              30d
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => void fetchActivity()}
            disabled={isRefreshing}
            className="gap-1.5"
          >
            <RefreshCwIcon className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/15 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {activity && (
        <>
          <ActivityMetricCards
            totalRuns={activity.total_sandbox_runs}
            activeStudents={activity.active_student_sessions}
            passRate={activity.overall_pass_rate}
            totalAiTokens={activity.total_ai_tokens}
            totalAiRequests={activity.total_ai_requests}
          />

          <ActivityVelocityChart
            velocity={activity.velocity}
            title="System-Wide Submission Velocity"
            description={`Hourly sandbox executions over the past ${windowHours >= 168 ? Math.round(windowHours / 24) + " days" : windowHours + " hours"}`}
          />

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <AttemptDistributionCard distribution={activity.attempt_distribution} />
            <ErrorBottlenecksCard bottlenecks={activity.top_bottlenecks} />
          </div>

          <AssignmentActivityTable assignments={activity.assignments} />
        </>
      )}
    </div>
  );
}
