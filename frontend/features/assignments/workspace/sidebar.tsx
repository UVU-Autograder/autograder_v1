"use client";

import { useState } from "react";
import {
  FileTextIcon,
  FolderIcon,
  FileCodeIcon,
  Trash2Icon,
  DownloadIcon,
  PlusIcon,
  ArchiveIcon,
} from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Assignment } from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { FileUploadButton } from "./file-upload-button";
import { useBasePath } from "@/lib/view-context";
import {
  downloadFile,
  downloadZipBundle,
  languageFromFilename,
} from "./file-utils";

export function AssignmentSidebar({
  courseId,
  className,
}: {
  assignment?: Assignment;
  courseId: string;
  className?: string;
}) {
  const basePath = useBasePath();
  const { files, openFileByName, uploadFiles, deleteFile } =
    useAssignmentFile();
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [newFileName, setNewFileName] = useState("");

  const workspaceFiles = Object.values(files)
    .filter((file) => file.category === "workspace")
    .map((file) => file.filename)
    .sort((a, b) => a.localeCompare(b));

  const handleCreateFile = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newFileName.trim();
    if (!trimmed) return;

    await openFileByName(trimmed, {
      content: "",
      language: languageFromFilename(trimmed),
      category: "workspace",
    });

    setNewFileName("");
    setIsCreatingFile(false);
  };

  return (
    <div
      className={`flex flex-col h-full w-full min-w-0 p-3 space-y-4 overflow-y-auto overflow-x-hidden bg-stone-50/90 border-r border-stone-200/80 ${className || ""}`}
    >
      {/* Header / BackLink */}
      <div className="px-1 pt-1">
        <BackLink
          href={
            basePath === "/sandbox"
              ? `/sandbox/${courseId}/assignments`
              : `/staff/courses/${courseId}/assignments`
          }
          variant="sidebar"
        >
          Back to assignments
        </BackLink>
      </div>

      {/* Details Button */}
      <div className="px-1">
        <button
          type="button"
          onClick={() =>
            openFileByName("Problem Overview", {
              content: "",
              language: "markdown",
              category: "overview",
            })
          }
          className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-stone-900 bg-white hover:bg-stone-100 border border-stone-200/80 rounded-md shadow-2xs transition-colors cursor-pointer"
        >
          <FileTextIcon className="size-4 text-indigo-600 shrink-0" />
          <span>Details</span>
        </button>
      </div>

      {/* Direct Files List */}
      <div className="space-y-2 px-1 pt-1 flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between">
          <div className="text-[11px] font-bold text-stone-500 uppercase tracking-wider flex items-center gap-1.5">
            <FolderIcon className="size-3.5 text-stone-500" />
            <span>Files</span>
          </div>
          <button
            type="button"
            onClick={() => setIsCreatingFile(true)}
            className="flex items-center gap-1 text-xs text-indigo-600 hover:text-indigo-800 font-semibold cursor-pointer p-0.5 rounded"
            title="New File"
          >
            <PlusIcon className="size-3.5" />
            <span>New</span>
          </button>
        </div>

        {isCreatingFile && (
          <form
            onSubmit={handleCreateFile}
            className="flex items-center gap-1 my-1"
          >
            <input
              type="text"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              placeholder="filename.py"
              autoFocus
              className="flex-1 min-w-0 px-2 py-1 text-xs border border-indigo-300 rounded font-mono focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              className="px-2 py-1 text-xs bg-indigo-600 text-white rounded font-medium hover:bg-indigo-700 cursor-pointer"
            >
              Add
            </button>
            <button
              type="button"
              onClick={() => {
                setNewFileName("");
                setIsCreatingFile(false);
              }}
              className="px-1.5 py-1 text-xs text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              ✕
            </button>
          </form>
        )}

        <div className="space-y-0.5 flex-1 overflow-y-auto min-h-0">
          {workspaceFiles.length > 0 ? (
            workspaceFiles.map((filename) => (
              <div
                key={filename}
                className="group/file flex items-center justify-between px-2 py-1.5 text-xs font-mono rounded-md hover:bg-stone-200/60 cursor-pointer"
              >
                <button
                  type="button"
                  onClick={() => openFileByName(filename)}
                  className="flex items-center gap-2 flex-1 min-w-0 text-left truncate cursor-pointer"
                >
                  <FileCodeIcon className="size-3.5 text-stone-500 shrink-0" />
                  <span className="truncate text-stone-800 font-medium">
                    {filename}
                  </span>
                </button>
                <div className="flex items-center gap-1 opacity-0 group-hover/file:opacity-100 transition-opacity">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (files[filename]) {
                        downloadFile(filename, files[filename].content);
                      }
                    }}
                    className="text-stone-600 hover:text-stone-900 p-0.5 rounded cursor-pointer"
                    title={`Download ${filename}`}
                  >
                    <DownloadIcon className="size-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteFile(filename);
                    }}
                    className="text-red-500 hover:text-red-700 p-0.5 rounded cursor-pointer"
                    title={`Delete ${filename}`}
                  >
                    <Trash2Icon className="size-3.5" />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <p className="py-1 text-xs text-stone-400 italic">
              No files added yet.
            </p>
          )}
        </div>

        <div className="pt-2 space-y-2 shrink-0">
          <FileUploadButton className="w-full" onFilesSelected={uploadFiles} />
          {workspaceFiles.length > 0 && (
            <button
              type="button"
              onClick={() => void downloadZipBundle(files)}
              className="w-full flex items-center justify-center gap-2 px-3 py-1.5 text-xs font-semibold text-stone-700 bg-white hover:bg-stone-100 border border-stone-200/80 rounded-md shadow-2xs transition-colors cursor-pointer"
            >
              <ArchiveIcon className="size-3.5 text-stone-600" />
              <span>Download ZIP</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default AssignmentSidebar;
