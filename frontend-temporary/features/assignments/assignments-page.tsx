'use client';

import MonacoEditor from "@/components/monaco-editor";
import { AssignmentsDataType } from "@/fakedata/assignments-reponse";
import CodeResults from "./code-results";
import { useAssignmentFile } from "./assingment-file-context";

export default function AssignmentsPage({ data }: { data: AssignmentsDataType }) {
  const { openFile } = useAssignmentFile();
  return (
    <div className="w-full h-full">
        <div className="flex flex-row w-full h-full">
            <div className="w-3/4 flex flex-col">
                <MonacoEditor
                key={openFile?.filename}
                height="100%"
                width="100%"
                defaultLanguage={openFile?.language || 'python'}
                defaultValue={openFile?.content || ''}
                className="flex-1"
                />
            </div>

            <div className="w-1/4 border-l border-gray-200 h-screen overflow-y-auto">
                <CodeResults data={data} />
            </div>
        </div>
    </div>
  );
}