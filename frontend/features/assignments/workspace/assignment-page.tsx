'use client';

import { useState } from "react";
import CodeResults from "./code-results";
import { useAssignmentFile } from "./assignment-file-context";
import { EditorSplitView } from "./editor-split-view";
import { AssignmentSidebar } from "./sidebar";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useIsMobile } from "@/hooks/use-mobile";
import { Code2Icon, FileTextIcon, PlayCircleIcon } from "lucide-react";

import type { AssignmentsDetails, Assignment } from "@/features/assignments/types";

type AssignmentsPageProps = {
  courseId: string;
  assignmentId: string;
  maxScore: number;
  initialQuota?: AssignmentsDetails["upload_quota"];
  assignment: Assignment;
};

export default function AssignmentWorkspace({
  courseId,
  assignmentId,
  maxScore,
  initialQuota,
  assignment,
}: AssignmentsPageProps) {
  const { layout } = useAssignmentFile();
  const isCompactLayout = useIsMobile(1024);
  const [mobileTab, setMobileTab] = useState<"files" | "editor" | "results">("editor");

  if (isCompactLayout) {
    return (
      <div className="flex h-full min-h-0 w-full flex-1 flex-col overflow-hidden bg-background">
        <Tabs
          value={mobileTab}
          onValueChange={(v) => setMobileTab(v as "files" | "editor" | "results")}
          className="flex h-full min-h-0 w-full flex-1 flex-col"
        >
          <div className="flex shrink-0 items-center border-b border-border bg-muted/40 px-3 py-1.5">
            <TabsList className="grid w-full grid-cols-3 h-8">
              <TabsTrigger value="files" className="flex items-center gap-1.5 text-xs">
                <FileTextIcon className="size-3.5" />
                <span>Files</span>
              </TabsTrigger>
              <TabsTrigger value="editor" className="flex items-center gap-1.5 text-xs">
                <Code2Icon className="size-3.5" />
                <span>Editor</span>
              </TabsTrigger>
              <TabsTrigger value="results" className="flex items-center gap-1.5 text-xs">
                <PlayCircleIcon className="size-3.5" />
                <span>Results</span>
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="files" className="h-full min-h-0 flex-1 overflow-auto m-0 p-0">
            <AssignmentSidebar assignment={assignment} courseId={courseId} />
          </TabsContent>

          <TabsContent value="editor" className="h-full min-h-0 flex-1 overflow-hidden m-0 p-0">
            <EditorSplitView layout={layout} />
          </TabsContent>

          <TabsContent value="results" className="h-full min-h-0 flex-1 overflow-auto m-0 p-0">
            <CodeResults
              courseId={courseId}
              assignmentId={assignmentId}
              maxScore={maxScore}
              initialQuota={initialQuota}
              assignment={assignment}
            />
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 w-full flex-1 overflow-hidden">
      <ResizablePanelGroup orientation="horizontal">
        <ResizablePanel defaultSize={25} minSize={10}>
          <AssignmentSidebar assignment={assignment} courseId={courseId} />
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel defaultSize={45} minSize={15}>
          <EditorSplitView layout={layout} />
        </ResizablePanel>

        <ResizableHandle withHandle />

        <ResizablePanel defaultSize={30} minSize={10}>
          <CodeResults
            courseId={courseId}
            assignmentId={assignmentId}
            maxScore={maxScore}
            initialQuota={initialQuota}
            assignment={assignment}
          />
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
