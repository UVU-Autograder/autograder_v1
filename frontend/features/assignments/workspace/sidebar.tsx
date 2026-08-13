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
  UploadIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
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
    const sanitized = trimmed.replace(/^(\.\.[/\\])+/, "").replace(/[/\\]/g, "_");
    if (!sanitized) return;

    await openFileByName(sanitized, {
      content: "",
      language: languageFromFilename(sanitized),
      category: "workspace",
    });

    setNewFileName("");
    setIsCreatingFile(false);
  };

  return (
    <div
      className={`flex flex-col h-full w-full min-w-0 p-3 space-y-4 overflow-y-auto overflow-x-hidden bg-slate-50 dark:bg-slate-950 border-r border-slate-200 dark:border-slate-800 ${className || ""}`}
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
        <Button
          variant="outline"
          size="sm"
          onClick={() =>
            openFileByName("Problem Overview", {
              content: "",
              language: "markdown",
              category: "overview",
            })
          }
          className="w-full justify-start text-xs font-semibold"
        >
          <FileTextIcon className="size-4 text-primary shrink-0" />
          <span>Details</span>
        </Button>
      </div>

      {/* Direct Files List */}
      <div className="space-y-2 px-1 pt-1 flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between pb-1 border-b border-border/50">
          <div className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
            <FolderIcon className="size-3.5" />
            <span>Files</span>
          </div>

          <div className="flex items-center gap-1">
            <FileUploadButton
              variant="ghost"
              size="xs"
              onFilesSelected={uploadFiles}
              className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground cursor-pointer"
              title="Upload files"
            >
              <UploadIcon className="size-3.5" />
            </FileUploadButton>

            {workspaceFiles.length > 0 && (
              <Button
                type="button"
                variant="ghost"
                size="xs"
                onClick={() => void downloadZipBundle(files)}
                className="h-6 px-1.5 text-xs text-muted-foreground hover:text-foreground cursor-pointer"
                title="Download ZIP"
              >
                <ArchiveIcon className="size-3.5" />
              </Button>
            )}

            <Button
              variant="ghost"
              size="xs"
              onClick={() => setIsCreatingFile(true)}
              className="h-6 px-1.5 text-xs text-primary hover:text-primary/80 font-semibold cursor-pointer"
              title="New File"
            >
              <PlusIcon className="size-3.5 mr-0.5" />
              <span>New</span>
            </Button>
          </div>
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
              className="flex-1 min-w-0 px-2 py-1 text-xs border border-primary/50 rounded font-mono bg-background text-foreground focus:outline-none focus:border-primary"
            />
            <Button
              type="submit"
              size="xs"
              className="h-6 px-2"
            >
              Add
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="icon-xs"
              onClick={() => {
                setNewFileName("");
                setIsCreatingFile(false);
              }}
              className="text-muted-foreground hover:text-foreground"
            >
              ✕
            </Button>
          </form>
        )}

        <div className="space-y-0.5 flex-1 overflow-y-auto min-h-0 pt-1">
          {workspaceFiles.length > 0 ? (
            workspaceFiles.map((filename) => (
              <div
                key={filename}
                onClick={() => openFileByName(filename)}
                className="group/file flex items-center justify-between px-2 py-1.5 text-xs font-mono rounded-md hover:bg-muted/70 cursor-pointer select-none"
              >
                <div className="flex items-center gap-2 flex-1 min-w-0 text-left truncate">
                  <FileCodeIcon className="size-3.5 text-muted-foreground shrink-0" />
                  <span className="truncate text-foreground font-medium">
                    {filename}
                  </span>
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover/file:opacity-100 transition-opacity">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (files[filename]) {
                        downloadFile(filename, files[filename].content);
                      }
                    }}
                    className="text-muted-foreground hover:text-foreground"
                    title={`Download ${filename}`}
                  >
                    <DownloadIcon className="size-3.5" />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteFile(filename);
                    }}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    title={`Delete ${filename}`}
                  >
                    <Trash2Icon className="size-3.5" />
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <p className="px-2 py-1.5 text-xs text-muted-foreground italic">
              No files added yet.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default AssignmentSidebar;
