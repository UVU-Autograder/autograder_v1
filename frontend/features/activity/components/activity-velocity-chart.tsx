import React, { useMemo } from "react";
import { ActivityTimeseriesPoint } from "../types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface ActivityVelocityChartProps {
  velocity: ActivityTimeseriesPoint[];
  title?: string;
  description?: string;
}

function formatBucketLabel(isoTimestamp: string): string {
  try {
    const d = new Date(isoTimestamp);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
    });
  } catch {
    return isoTimestamp;
  }
}

export function ActivityVelocityChart({
  velocity,
  title = "Submission Velocity",
  description = "Student practice run volume and peak submission windows",
}: ActivityVelocityChartProps) {
  const maxRuns = useMemo(
    () => Math.max(...velocity.map((v) => v.run_count), 1),
    [velocity]
  );

  if (velocity.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No sandbox submissions in this time window.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex h-44 items-end gap-1.5 pt-4 pb-2 border-b border-border">
          {velocity.map((point, idx) => {
            const heightPercent = Math.max(Math.round((point.run_count / maxRuns) * 100), point.run_count > 0 ? 6 : 2);
            const passPercent = point.run_count > 0 ? Math.round((point.success_count / point.run_count) * 100) : 0;
            const failPercent = 100 - passPercent;

            return (
              <div
                key={point.timestamp || idx}
                className="group relative flex flex-1 flex-col items-center justify-end h-full min-w-4"
              >
                {/* Tooltip */}
                <div className="pointer-events-none absolute -top-12 z-20 hidden rounded bg-popover px-2 py-1 text-xs text-popover-foreground shadow-md border group-hover:block whitespace-nowrap">
                  <div className="font-semibold">{formatBucketLabel(point.timestamp)}</div>
                  <div className="tabular-nums">
                    {point.run_count} runs ({point.success_count} passed, {point.failure_count} failed)
                  </div>
                </div>

                {/* Bar */}
                <div
                  className="w-full rounded-t transition-all flex flex-col justify-end overflow-hidden bg-muted"
                  style={{ height: `${heightPercent}%` }}
                >
                  {point.failure_count > 0 && (
                    <div
                      className="w-full bg-destructive/80 transition-all"
                      style={{ height: `${failPercent}%` }}
                    />
                  )}
                  {point.success_count > 0 && (
                    <div
                      className="w-full bg-primary/80 transition-all"
                      style={{ height: `${passPercent}%` }}
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* X-axis labels */}
        <div className="mt-2 flex justify-between text-[11px] text-muted-foreground tabular-nums">
          <span>{formatBucketLabel(velocity[0]?.timestamp)}</span>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-primary/80" /> Passed
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-destructive/80" /> Failed
            </span>
          </div>
          <span>{formatBucketLabel(velocity[velocity.length - 1]?.timestamp)}</span>
        </div>
      </CardContent>
    </Card>
  );
}
