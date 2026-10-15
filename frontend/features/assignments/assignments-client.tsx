"use client";

import { useEffect, useState } from "react";
import SandboxLoading from "@/app/sandbox/loading";
import StaffLoading from "@/app/staff/loading";
import { Button } from "@/components/ui/button";
import { getAssignments } from "@/features/assignments/api";
import AssignmentsPage from "@/features/assignments/assignments-page";
import { AssignmentsResponse } from "@/features/assignments/types";

export default function AssignmentsClient({ courseId, mode }: { courseId: string; mode: "sandbox" | "staff" }) {
  const [data, setData] = useState<AssignmentsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    getAssignments(courseId)
      .then(setData)
      .catch(() => setError("Failed to load assignments."));
  }, [courseId, attempt]);

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
  if (!data) {
    return mode === "sandbox" ? <SandboxLoading /> : <StaffLoading />;
  }
  return <AssignmentsPage data={data} mode={mode} />;
}
