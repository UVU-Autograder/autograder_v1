'use client';

import { AssignmentsDataType } from "@/fakedata/assignments-reponse";
import CodeResults from "./code-results";
import { useAssignmentFile } from "./assingment-file-context";
import { EditorSplitView } from "./editor-split-view";

export default function AssignmentsPage({ data }: { data: AssignmentsDataType }) {
  const { layout } = useAssignmentFile();
  
  return (
    <div className="w-full h-full">
        <div className="flex flex-row h-screen">
            <div className="w-3/4 flex flex-col min-h-0">
                <EditorSplitView layout={layout} />
            </div>

            <div className="w-1/4 border-l border-gray-200 h-screen overflow-y-auto">
                <CodeResults data={data} />
            </div>
        </div>
    </div>
  );
}
