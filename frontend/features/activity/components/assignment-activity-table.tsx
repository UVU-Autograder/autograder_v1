import React from "react";
import Link from "next/link";
import { AssignmentActivitySummary } from "../types";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface AssignmentActivityTableProps {
  assignments: AssignmentActivitySummary[];
  courseCode?: string;
}

export function AssignmentActivityTable({
  assignments,
  courseCode,
}: AssignmentActivityTableProps) {
  if (assignments.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Assignment Engagement</CardTitle>
          <CardDescription>Practice activity broken down by assignment</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No assignment-level activity recorded in this window.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Assignment Engagement</CardTitle>
        <CardDescription>Practice activity, student counts, and pass rates by assignment</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border text-xs text-muted-foreground uppercase">
              <tr>
                <th className="py-2.5 font-medium">Assignment</th>
                <th className="py-2.5 text-right font-medium">Students</th>
                <th className="py-2.5 text-right font-medium">Practice Runs</th>
                <th className="py-2.5 text-right font-medium">Pass Rate</th>
                <th className="py-2.5 text-right font-medium">Top Bottleneck</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {assignments.map((assignment) => {
                const targetCourse = courseCode || "cs1410";
                const href = `/staff/courses/${targetCourse}/assignments/${assignment.assignment_code}`;

                return (
                  <tr key={assignment.assignment_id} className="hover:bg-muted/40 transition-colors">
                    <td className="py-2.5 pr-4">
                      <Link href={href} className="font-medium text-foreground hover:underline">
                        {assignment.title}
                      </Link>
                      <span className="ml-2 font-mono text-xs text-muted-foreground">
                        ({assignment.assignment_code})
                      </span>
                    </td>
                    <td className="py-2.5 text-right tabular-nums text-foreground">
                      {assignment.active_students}
                    </td>
                    <td className="py-2.5 text-right tabular-nums text-foreground">
                      {assignment.total_runs}
                    </td>
                    <td className="py-2.5 text-right tabular-nums">
                      <span
                        className={
                          assignment.pass_rate >= 80
                            ? "text-success font-medium"
                            : assignment.pass_rate >= 50
                            ? "text-warning font-medium"
                            : "text-destructive font-medium"
                        }
                      >
                        {assignment.pass_rate}%
                      </span>
                    </td>
                    <td className="py-2.5 text-right">
                      {assignment.top_bottleneck ? (
                        <span className="font-mono text-xs text-muted-foreground">
                          {assignment.top_bottleneck}
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
