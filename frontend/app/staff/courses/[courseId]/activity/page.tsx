"use client";

import { useCallback, useEffect, useState, use } from "react";
import { RefreshCwIcon } from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageLoading } from "@/components/page-status";
import { Button } from "@/components/ui/button";
import { getCourseActivity } from "@/features/activity/api";
import type { CourseActivityResponse } from "@/features/activity/types";
import { ActivityMetricCards } from "@/features/activity/components/activity-metric-cards";
import { ActivityVelocityChart } from "@/features/activity/components/activity-velocity-chart";
import { AttemptDistributionCard } from "@/features/activity/components/attempt-distribution-card";
import { ErrorBottlenecksCard } from "@/features/activity/components/error-bottlenecks-card";
import { AssignmentActivityTable } from "@/features/activity/components/assignment-activity-table";

interface PageProps {
  params: Promise<{ courseId: string }>;
}

export default function CourseActivityPage({ params }: PageProps) {
  const { courseId } = use(params);
  const [activity, setActivity] = useState<CourseActivityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [windowHours, setWindowHours] = useState<number>(168);

  const fetchActivity = useCallback(async (hours = windowHours) => {
    setIsRefreshing(true);
    setError(null);
    try {
      const data = await getCourseActivity(courseId, hours);
      setActivity(data);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to load course activity telemetry.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [courseId, windowHours]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setError(null);
      try {
        const data = await getCourseActivity(courseId, windowHours);
        if (!cancelled) setActivity(data);
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          setError(err instanceof Error ? err.message : "Failed to load course activity telemetry.");
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
  }, [courseId, windowHours]);

  if (isLoading) {
    return <PageLoading className="h-screen">Loading course activity telemetry...</PageLoading>;
  }

  const courseTitle = activity?.course_title || courseId.toUpperCase();

  return (
    <div className="mx-auto w-full max-w-5xl px-4 pt-8 pb-16 space-y-6">
      <Breadcrumbs
        items={[
          { label: "Courses", href: "/staff/courses" },
          { label: courseTitle, href: `/staff/courses/${courseId}/assignments` },
          { label: "Activity Monitor" },
        ]}
      />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
        <AdminPageHeader
          title={`${courseTitle} Activity Monitor`}
          description={`Student practice volume, submission velocity, attempt distributions, and error bottlenecks for ${courseId.toUpperCase()}`}
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
            title={`${courseId.toUpperCase()} Submission Velocity`}
            description={`Student practice submissions leading up to assignment deadlines`}
          />

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <AttemptDistributionCard distribution={activity.attempt_distribution} />
            <ErrorBottlenecksCard bottlenecks={activity.top_bottlenecks} />
          </div>

          <AssignmentActivityTable
            assignments={activity.assignments}
            courseCode={courseId}
          />
        </>
      )}
    </div>
  );
}
