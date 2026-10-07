"use client";

import { useMemo, useState } from "react";
import {
  FileTextIcon,
  FolderIcon,
  FileCodeIcon,
  Trash2Icon,
  DownloadIcon,
  PlusIcon,
  ArchiveIcon,
  UploadIcon,
  PencilIcon,
  CheckIcon,
  XIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { BackLink } from "@/components/back-link";
import { Assignment } from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { FileUploadButton } from "./file-upload-button";
import { useBasePath } from "@/lib/view-context";
import {
  checkBundleRequirements,
  downloadFile,
  downloadZipBundle,
  languageFromFilename,
  sanitizeFilename,
  validateFilename,
} from "./file-utils";

export function AssignmentSidebar({
  assignment: propAssignment,
  courseId,
  className,
}: {
  assignment?: Assignment;
  courseId: string;
  className?: string;
}) {
  const basePath = useBasePath();
  const {
    files,
    openFileByName,
    uploadFiles,
    deleteFile,
    renameFile,
    assignment: contextAssignment,
  } = useAssignmentFile();
  const assignment = propAssignment ?? contextAssignment;

  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [newFileName, setNewFileName] = useState("");
  const [renamingFilename, setRenamingFilename] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [renameError, setRenameError] = useState<string | null>(null);

  const workspaceFiles = useMemo(
    () =>
      Object.values(files)
        .filter((file) => file.category === "workspace")
        .map((file) => file.filename)
        .sort((a, b) => a.localeCompare(b)),
    [files]
  );

  const bundleStatus = useMemo(
    () => checkBundleRequirements(files, assignment),
    [files, assignment]
  );

  const handleCreateFile = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newFileName.trim();
    if (!trimmed) return;
    const sanitized = sanitizeFilename(trimmed);
    if (!sanitized) return;

    await openFileByName(sanitized, {
      content: "",
      language: languageFromFilename(sanitized),
      category: "workspace",
    });

    setNewFileName("");
    setIsCreatingFile(false);
  };

  const handleStartRename = (filename: string) => {
    setRenamingFilename(filename);
    setRenameDraft(filename);
    setRenameError(null);
  };

  const handleRenameInputChange = (val: string) => {
    setRenameDraft(val);
    const validation = validateFilename(
      val,
      workspaceFiles,
      renamingFilename ?? undefined
    );
    if (!validation.valid) {
      setRenameError(validation.error ?? "Invalid filename.");
    } else {
      setRenameError(null);
    }
  };

  const handleCommitRename = () => {
    if (!renamingFilename) return;
    const trimmed = renameDraft.trim();
    if (trimmed === renamingFilename) {
      setRenamingFilename(null);
      setRenameDraft("");
      setRenameError(null);
      return;
    }
    const validation = validateFilename(
      trimmed,
      workspaceFiles,
      renamingFilename
    );
    if (!validation.valid) {
      setRenameError(validation.error ?? "Invalid filename.");
      return;
    }
    const success = renameFile(renamingFilename, trimmed);
    if (success) {
      setRenamingFilename(null);
      setRenameDraft("");
      setRenameError(null);
    } else {
      setRenameError("Failed to rename file.");
    }
  };

  const handleCancelRename = () => {
    setRenamingFilename(null);
    setRenameDraft("");
    setRenameError(null);
  };

  return (
    <div
      className={`flex flex-col h-full w-full min-w-0 p-3 space-y-4 overflow-y-auto overflow-x-hidden bg-card border-r border-border ${className || ""}`}
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
          <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
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
            workspaceFiles.map((filename) =>
              renamingFilename === filename ? (
                <form
                  key={filename}
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleCommitRename();
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="flex flex-col gap-1 w-full p-1.5 border border-primary/50 rounded-md bg-background my-0.5"
                >
                  <div className="flex items-center gap-1">
                    <input
                      type="text"
                      value={renameDraft}
                      onChange={(e) => handleRenameInputChange(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Escape") {
                          e.preventDefault();
                          handleCancelRename();
                        }
                      }}
                      autoFocus
                      className="flex-1 min-w-0 px-1.5 py-0.5 text-xs border border-primary/50 rounded font-mono bg-background text-foreground focus:outline-none focus:border-primary"
                    />
                    <Button
                      type="submit"
                      variant="ghost"
                      size="icon-xs"
                      disabled={Boolean(renameError)}
                      className="h-6 w-6 text-primary hover:text-primary hover:bg-primary/10 disabled:opacity-40"
                      title="Save rename"
                    >
                      <CheckIcon className="size-3.5" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-xs"
                      onClick={handleCancelRename}
                      className="h-6 w-6 text-muted-foreground hover:text-foreground"
                      title="Cancel rename"
                    >
                      <XIcon className="size-3.5" />
                    </Button>
                  </div>
                  {renameError && (
                    <span className="text-[10px] text-destructive px-1 leading-tight">
                      {renameError}
                    </span>
                  )}
                </form>
              ) : (
                <div
                  key={filename}
                  onClick={() => openFileByName(filename)}
                  className="group/file flex items-center justify-between px-2 py-1.5 text-xs font-mono rounded-md hover:bg-muted/70 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-1.5 flex-1 min-w-0 text-left truncate">
                    <FileCodeIcon className="size-3.5 text-muted-foreground shrink-0" />
                    <span className="truncate text-foreground font-medium">
                      {filename}
                    </span>
                    {bundleStatus.expectedEntrypoint === filename && (
                      <span className="text-[9px] uppercase font-sans tracking-wide px-1 py-0.2 rounded bg-primary/10 text-primary border border-primary/20 shrink-0 font-medium">
                        entrypoint
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover/file:opacity-100 transition-opacity">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStartRename(filename);
                      }}
                      className="text-muted-foreground hover:text-foreground"
                      title={`Rename ${filename}`}
                    >
                      <PencilIcon className="size-3.5" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (files[filename]) {
                          downloadFile(
                            filename,
                            files[filename].content,
                            files[filename].kind
                          );
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
              )
            )
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
