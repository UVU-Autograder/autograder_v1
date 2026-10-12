"use client";

import { useEffect, useState } from "react";
import Loading from "@/app/sandbox/loading";
import { Button } from "@/components/ui/button";
import { getAssignment } from "@/features/assignments/api";
import { Assignment } from "@/features/assignments/types";
import AssignmentWorkspace from "@/features/assignments/workspace/assignment-page";
import { AssignmentFileProvider } from "@/features/assignments/workspace/assignment-file-context";

export default function AssignmentClient({ courseId, assignmentId }: { courseId: string; assignmentId: string }) {
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    // In the browser this sends the student's stored sandbox session, so upload_quota is theirs.
    getAssignment(courseId, assignmentId)
      .then(setAssignment)
      .catch(() => setError("Failed to load assignment."));
  }, [courseId, assignmentId, attempt]);

  if (error) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-6">
        <p className="text-center text-muted-foreground">{error}</p>
        <Button
          onClick={() => {
            setError(null);
            setAttempt((n) => n + 1);
          }}
        >
          Try again
        </Button>
      </div>
    );
  }
  if (!assignment) {
    return <Loading />;
  }
  return (
    <AssignmentFileProvider assignment={assignment}>
        <div className="h-full w-full min-h-0 flex flex-1 flex-col overflow-hidden">
            <AssignmentWorkspace
              courseId={courseId}
              assignmentId={assignmentId}
              maxScore={assignment.max_score}
              initialQuota={assignment.upload_quota}
              assignment={assignment}
            />
        </div>
    </AssignmentFileProvider>
  );
}
