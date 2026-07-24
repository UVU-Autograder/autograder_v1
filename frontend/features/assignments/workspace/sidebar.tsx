'use client';

import { FileTextIcon, FolderIcon, FileCodeIcon, Trash2Icon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Assignment } from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { FileUploadButton } from "./file-upload-button";
import { useBasePath } from "@/lib/view-context";

export function AssignmentSidebar({
    assignment,
    courseId,
    className
}: {
    assignment: Assignment;
    courseId: string;
    className?: string;
}) {
    const basePath = useBasePath();
    const { files, openFileByName, uploadFiles, deleteFile } = useAssignmentFile();

    const workspaceFiles = Object.values(files)
        .filter((file) => file.category === 'workspace')
        .map((file) => file.filename)
        .sort((a, b) => a.localeCompare(b));

    return (
        <div className={`flex flex-col h-full w-full min-w-0 p-3 space-y-4 overflow-y-auto overflow-x-hidden bg-stone-50/90 border-r border-stone-200/80 ${className || ''}`}>
            {/* Header / BackLink */}
            <div className="px-1 pt-1">
                <BackLink
                    href={basePath === "/sandbox" ? `/sandbox/${courseId}/assignments` : `/staff/courses/${courseId}/assignments`}
                    variant="sidebar"
                >
                    Back to assignments
                </BackLink>
            </div>

            {/* Details Button */}
            <div className="px-1">
                <button
                    type="button"
                    onClick={() => openFileByName("Problem Overview", { content: "", language: 'markdown', category: 'overview' })}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-stone-900 bg-white hover:bg-stone-100 border border-stone-200/80 rounded-md shadow-2xs transition-colors cursor-pointer"
                >
                    <FileTextIcon className="size-4 text-indigo-600 shrink-0" />
                    <span>Details</span>
                </button>
            </div>

            {/* Direct Files List */}
            <div className="space-y-2 px-1 pt-1 flex-1">
                <div className="text-[11px] font-bold text-stone-500 uppercase tracking-wider flex items-center gap-1.5">
                    <FolderIcon className="size-3.5 text-stone-500" />
                    <span>Files</span>
                </div>
                <div className="space-y-0.5">
                    {workspaceFiles.length > 0 ? (
                        workspaceFiles.map((filename) => (
                            <div key={filename} className="group/file flex items-center justify-between px-2 py-1.5 text-xs font-mono rounded-md hover:bg-stone-200/60 cursor-pointer">
                                <button
                                    type="button"
                                    onClick={() => openFileByName(filename)}
                                    className="flex items-center gap-2 flex-1 min-w-0 text-left truncate cursor-pointer"
                                >
                                    <FileCodeIcon className="size-3.5 text-stone-500 shrink-0" />
                                    <span className="truncate text-stone-800 font-medium">{filename}</span>
                                </button>
                                <button
                                    type="button"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        deleteFile(filename);
                                    }}
                                    className="opacity-0 group-hover/file:opacity-100 text-red-500 hover:text-red-700 transition-opacity p-0.5 rounded cursor-pointer"
                                    title={`Delete ${filename}`}
                                >
                                    <Trash2Icon className="size-3.5" />
                                </button>
                            </div>
                        ))
                    ) : (
                        <p className="py-1 text-xs text-stone-400 italic">No files uploaded yet.</p>
                    )}
                </div>
                <div className="pt-2">
                    <FileUploadButton
                        className="w-full"
                        onFilesSelected={uploadFiles}
                    />
                </div>
            </div>
        </div>
    );
}

export default AssignmentSidebar;
