'use client';

import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"

import MonacoEditor from "@/components/monaco-editor";
import { Button } from "@/components/ui/button";
import { AssignmentsSidebar } from "./sidebar";
import { assignmentsCodeExample } from "@/fakedata/assignments-code-example";
import { AssignmentsDataType } from "@/fakedata/assignments-reponse";

export default function AssignmentsPage({ data }: { data: AssignmentsDataType }) {
  const handleCheckCode = () => {
    document.getElementById("feedback")!.classList.toggle("hidden");
  }

  return (
    <div id="root" className="w-full h-full">
      <SidebarProvider>
      <AssignmentsSidebar />
      <SidebarInset>
        <div className="flex flex-row w-full h-full">
            <div className="w-3/4">
                <MonacoEditor height="100vh" width="100%" defaultLanguage="python" defaultValue={assignmentsCodeExample.code} className="" />
            </div>

            <div className="w-1/4 border-l border-gray-200 h-screen overflow-y-auto">

            <Button onClick={handleCheckCode} className="w-full mt-2">Check Code</Button>

            <div id="feedback" className="display flex flex-1 flex-col">
                <div className="p-2 gap-2">
                    <pre className="text-wrap">
                        <p className="font-bold text-lg">Feedback:</p>
                        <p>Score: {data.response.data.projected_result.projected_score}</p>
                        <p>{data.response.data.projected_result.feedback.summary}</p>
                    </pre>

                    <pre className="text-wrap">
                        <p className="font-bold text-lg">Test Cases:</p>
                        <p>{JSON.stringify(data.response.data.projected_result.test_results, null, 2)}</p>
                    </pre>

                    <pre className="text-wrap">
                        <p className="font-bold text-lg">Constraints Violations:</p>
                        <p>{JSON.stringify(data.response.data.projected_result.constraint_result.warnings, null, 2)}</p>
                    </pre>
                </div>
            </div>
            </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
    </div>
  );
}