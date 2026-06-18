'use client';

import { AssignmentsDataType } from "@/fakedata/assignments-reponse";
import CodeResults from "./code-results";
import { useAssignmentFile } from "./assingment-file-context";
import { EditorSplitView } from "./editor-split-view";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"


export default function AssignmentsPage({ data }: { data: AssignmentsDataType }) {
  const { layout } = useAssignmentFile();
  
  return (
    <div className="flex h-full min-h-0 w-full flex-1 flex-col">
		<ResizablePanelGroup orientation="horizontal" className="min-h-0 w-full flex-1">
			<ResizablePanel defaultSize={75} minSize={50} className="flex min-h-0">
					<EditorSplitView layout={layout} />
			</ResizablePanel>
			<ResizableHandle withHandle />
			<ResizablePanel defaultSize={25} minSize={0} className="overflow-y-auto">
				<CodeResults data={data} />
			</ResizablePanel>
        </ResizablePanelGroup>
    </div>
  );
}
