import Link from "next/link";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageEmpty } from "@/components/page-status";
import { Button } from "@/components/ui/button";
import { AssignmentsResponse } from "@/features/assignments/types";
import AssignmentCard from "@/features/assignments/assignment-card";

type ViewMode = "sandbox" | "staff";

export default function AssignmentsPage({
  data,
  mode,
}: {
  data: AssignmentsResponse;
  mode: ViewMode;
}) {
  const coursesHref = mode === "sandbox" ? "/sandbox" : "/staff/courses";

  // Group assignments by module_name
  const grouped = data.assignments.reduce<Record<string, typeof data.assignments>>((acc, assignment) => {
    const key = assignment.module_name || "Unassigned";
    if (!acc[key]) acc[key] = [];
    acc[key].push(assignment);
    return acc;
  }, {});

  const groupKeys = Object.keys(grouped);
  const hasModules = groupKeys.some(k => k !== "Unassigned");

  // Sort keys so modules are ordered, and "Unassigned" comes last
  const sortedGroupKeys = groupKeys.sort((a, b) => {
    if (a === "Unassigned") return 1;
    if (b === "Unassigned") return -1;
    return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
  });

  return (
    <div className="w-full px-4 pt-8">
      <div className="mb-6">
        <Breadcrumbs
          items={[
            { label: "Courses", href: coursesHref },
            { label: "Assignments" },
          ]}
        />
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Assignments</h1>
            <p className="mt-1 text-xs font-semibold text-primary tracking-wider uppercase">
              {data.course_id}
            </p>
          </div>
          {mode === "staff" && (
            <div className="flex gap-2">
              <Button variant="outline" asChild>
                <Link href={`/staff/courses/${data.course_id}/settings`}>
                  Course Settings
                </Link>
              </Button>
              <Button asChild>
                <Link href={`/staff/courses/${data.course_id}/assignments/new`}>
                  New Assignment
                </Link>
              </Button>
            </div>
          )}
        </div>
      </div>

      {data.assignments.length === 0 ? (
        <PageEmpty>No assignments available yet.</PageEmpty>
      ) : hasModules ? (
        <div className="space-y-8">
          {sortedGroupKeys.map((groupKey) => (
            <div key={groupKey} className="space-y-3">
              <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase border-b border-border pb-1">
                {groupKey}
              </h2>
              <div className="flex w-full flex-col gap-2">
                {grouped[groupKey].map((assignment) => (
                  <AssignmentCard
                    key={assignment.id}
                    assignment={assignment}
                    courseId={data.course_id}
                    mode={mode}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex w-full flex-col gap-2">
          {data.assignments.map((assignment) => (
            <AssignmentCard
              key={assignment.id}
              assignment={assignment}
              courseId={data.course_id}
              mode={mode}
            />
          ))}
        </div>
      )}
    </div>
  );
}
