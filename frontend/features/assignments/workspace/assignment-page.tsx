'use client';

import CodeResults from "./code-results";
import { useAssignmentFile } from "./assignment-file-context";
import { EditorSplitView } from "./editor-split-view";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"

import type { AssignmentsDetails } from "@/features/assignments/types";

type AssignmentsPageProps = {
  courseId: string;
  assignmentId: string;
  maxScore: number;
  initialQuota?: AssignmentsDetails["upload_quota"];
};

export default function AssignmentsPage({
  courseId,
  assignmentId,
  maxScore,
  initialQuota,
}: AssignmentsPageProps) {
  const { layout } = useAssignmentFile();
  
  return (
    <div className="flex h-full min-h-0 w-full flex-1 flex-col">
		<ResizablePanelGroup orientation="horizontal" className="min-h-0 w-full flex-1">
			<ResizablePanel defaultSize={75} minSize={50} className="flex min-h-0">
					<EditorSplitView layout={layout} />
			</ResizablePanel>
			<ResizableHandle withHandle />
			<ResizablePanel defaultSize={25} minSize={0} className="overflow-y-auto">
				<CodeResults
          courseId={courseId}
          assignmentId={assignmentId}
          maxScore={maxScore}
          initialQuota={initialQuota}
        />
			</ResizablePanel>
        </ResizablePanelGroup>
    </div>
  );
}
