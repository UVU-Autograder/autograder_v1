"use client";

import React, { use } from "react";
import { AssignmentEditorProvider } from "@/features/assignments/components/editor/assignment-editor-context";
import { AssignmentEditor } from "@/features/assignments/components/editor/assignment-editor";

interface PageProps {
  params: Promise<{
    courseId: string;
    assignmentId: string;
  }>;
}

export default function StaffAssignmentPage({ params }: PageProps) {
  const resolvedParams = use(params);

  return (
    <AssignmentEditorProvider
      courseId={resolvedParams.courseId}
      assignmentId={resolvedParams.assignmentId}
    >
      <div className="container mx-auto max-w-6xl p-6">
        <AssignmentEditor />
      </div>
    </AssignmentEditorProvider>
  );
}
