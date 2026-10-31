import React from "react";
import { UsersIcon, ActivityIcon, CheckCircle2Icon, SparklesIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface ActivityMetricCardsProps {
  totalRuns: number;
  activeStudents: number;
  passRate: number;
  totalAiTokens: number;
  totalAiRequests: number;
}

export function ActivityMetricCards({
  totalRuns,
  activeStudents,
  passRate,
  totalAiTokens,
  totalAiRequests,
}: ActivityMetricCardsProps) {
  const avgRunsPerStudent = activeStudents > 0 ? (totalRuns / activeStudents).toFixed(1) : "0";

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <Card>
        <CardContent className="pt-5 pb-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Active Students</span>
            <UsersIcon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-2 text-2xl font-semibold tabular-nums text-foreground">
            {activeStudents}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Unique student sessions</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5 pb-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Total Practice Runs</span>
            <ActivityIcon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-2 text-2xl font-semibold tabular-nums text-foreground">
            {totalRuns}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Avg {avgRunsPerStudent} runs / student</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5 pb-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Overall Pass Rate</span>
            <CheckCircle2Icon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-2 text-2xl font-semibold tabular-nums text-foreground">
            {passRate}%
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Passing test outcomes</p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-5 pb-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">AI Coaching</span>
            <SparklesIcon className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="mt-2 text-2xl font-semibold tabular-nums text-foreground">
            {totalAiRequests}
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{totalAiTokens.toLocaleString()} tokens served</p>
        </CardContent>
      </Card>
    </div>
  );
}
