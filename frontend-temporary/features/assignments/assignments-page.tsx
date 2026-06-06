'use client';

import MonacoEditor from "@/components/monaco-editor";
import { AssignmentsDataType } from "@/fakedata/assignments-reponse";
import CodeResults from "./code-results";
import { useAssignmentFile } from "./assingment-file-context";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { XIcon } from "lucide-react";

export default function AssignmentsPage({ data }: { data: AssignmentsDataType }) {
  const { openFiles, activeFile, setActiveFile, closeFile } = useAssignmentFile();
  
  return (
    <div className="w-full h-full">
        <div className="flex flex-row h-screen">
            <div className="w-3/4 flex flex-col min-h-0">
                {openFiles.length > 0 && activeFile && (
                    <Tabs
                        value={activeFile}
                        onValueChange={setActiveFile}
                        className="flex flex-1 flex-col min-h-0 gap-0 p-0"
                    >
                        <TabsList className="w-full shrink-0 justify-start rounded-none p-0">
                            {openFiles.map((file) => (
                                <div
                                    key={file.filename}
                                    className="inline-flex items-stretch border-r border-border last:border-r-0 data-[active=true]:bg-background"
                                    data-active={activeFile === file.filename}
                                    onMouseDown={(event) => {
                                        if (event.button === 1) {
                                            event.preventDefault();
                                            closeFile(file.filename);
                                        }
                                    }}
                                >
                                    <TabsTrigger
                                        className="rounded-none flex-none max-w-48 px-4 py-2"
                                        value={file.filename}
                                    >
                                        <span className="truncate">{file.filename}</span>
                                    </TabsTrigger>
                                    <button
                                        type="button"
                                        aria-label={`Close ${file.filename}`}
                                        className="inline-flex items-center justify-center px-1.5 opacity-60 transition-opacity hover:bg-muted hover:opacity-100"
                                        onClick={() => closeFile(file.filename)}
                                    >
                                        <XIcon className="size-3.5" />
                                    </button>
                                </div>
                            ))}
                        </TabsList>
                        {openFiles.map((file) => (
                            <TabsContent
                                key={file.filename}
                                value={file.filename}
                                className="flex-1 min-h-0 mt-0"
                            >
                                <MonacoEditor
                                    key={file.filename}
                                    height="100%"
                                    width="100%"
                                    defaultLanguage={file.language || 'python'}
                                    defaultValue={file.content || ''}
                                />
                            </TabsContent>
                        ))}
                    </Tabs>
                )}
            </div>

            <div className="w-1/4 border-l border-gray-200 h-screen overflow-y-auto">
                <CodeResults data={data} />
            </div>
        </div>
    </div>
  );
}