"use client";

import React, { useState } from "react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import MonacoEditor from "@/components/monaco-editor";
import {
  SaveIcon,
  Trash2Icon,
  CheckCircle2Icon,
  ShieldAlertIcon,
  CopyIcon,
  CheckIcon,
  FileTextIcon,
  XIcon,
  PlayIcon,
  RotateCcwIcon,
} from "lucide-react";
import Link from "next/link";
import { useAssignmentEditor } from "./assignment-editor-context";
import { MetadataSection } from "./metadata-section";
import { ScoringRulesSection } from "./scoring-rules-section";
import { ModelSolutionSection } from "./model-solution-section";

export function AssignmentEditor() {
  const {
    courseId,
    assignmentId,
    loading,
    saving,
    dirty,
    saveSuccess,
    errorMessage,
    successMessage,
    title,
    handleSave,
    handleDiscard,
    handleDelete,
    handleCopyStudentLink,
    copiedLink,

    // Code modal
    isCodeModalOpen,
    setIsCodeModalOpen,
    editArtifactFilename,
    editCodeText,
    setEditCodeText,
    isLoadingCode,
    isSavingCode,
    saveCodeChanges,
  } = useAssignmentEditor();

  const [activeTab, setActiveTab] = useState("metadata");

  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center text-sm text-muted-foreground animate-pulse">
        Loading…
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3 border-b border-border pb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <BackLink href={`/staff/courses/${courseId}/assignments`}>
            Back to assignments
          </BackLink>

          <div className="flex max-w-full flex-nowrap items-center gap-2 overflow-x-auto sm:justify-end">
            <span
              className={`flex min-w-[9.5rem] items-center justify-end gap-1 text-xs font-medium whitespace-nowrap ${
                saveSuccess
                  ? "text-success"
                  : dirty
                    ? "text-warning"
                    : "invisible"
              }`}
              aria-live="polite"
            >
              {saveSuccess ? (
                <>
                  <CheckCircle2Icon className="h-4 w-4" />
                  Saved
                </>
              ) : (
                "Unsaved changes"
              )}
            </span>

            <Button
              variant="outline"
              size="sm"
              onClick={() => void handleDiscard()}
              disabled={!dirty || saving || loading}
            >
              <RotateCcwIcon className="h-4 w-4" />
              Discard
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleSave}
              disabled={saving || !dirty}
              className="min-w-[5.5rem]"
            >
              <SaveIcon className="h-4 w-4" />
              {saving ? "Saving..." : "Save"}
            </Button>

            <span aria-hidden className="mx-1 h-5 w-px shrink-0 bg-border" />

            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyStudentLink}
              className="min-w-[8.25rem]"
            >
              {copiedLink ? (
                <>
                  <CheckIcon className="h-4 w-4 text-success" />
                  Copied
                </>
              ) : (
                <>
                  <CopyIcon className="h-4 w-4" />
                  Student link
                </>
              )}
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link
                href={`/staff/courses/${courseId}/assignments/${assignmentId}/runs`}
              >
                <PlayIcon className="h-4 w-4" />
                Grade
              </Link>
            </Button>

            <span aria-hidden className="mx-1 h-5 w-px shrink-0 bg-border" />

            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              className="text-destructive border-destructive/30 hover:bg-destructive/10"
            >
              <Trash2Icon className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>

        <h1 className="text-balance text-2xl font-bold tracking-tight text-foreground">
          {title || assignmentId}
        </h1>
      </div>

      {errorMessage && (
        <div className="flex items-start gap-2 whitespace-pre-line rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          <ShieldAlertIcon className="mt-0.5 h-5 w-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-success/30 bg-success/10 p-3 text-sm text-success">
          <CheckCircle2Icon className="h-5 w-5 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full max-w-2xl grid-cols-3 rounded-lg bg-muted p-1">
          <TabsTrigger value="metadata">General & Files</TabsTrigger>
          <TabsTrigger value="rubrics">Test Suite & Rubric</TabsTrigger>
          <TabsTrigger value="model_solution">Model Solution</TabsTrigger>
        </TabsList>

        <TabsContent value="metadata">
          <MetadataSection />
        </TabsContent>

        <TabsContent value="rubrics">
          <ScoringRulesSection />
        </TabsContent>

        <TabsContent value="model_solution">
          <ModelSolutionSection />
        </TabsContent>
      </Tabs>

      {/* Code Editor Modal Overlay */}
      {isCodeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-fade-in" role="dialog" aria-modal="true">
          <div className="bg-card rounded-lg border border-border shadow-xl w-full max-w-5xl h-[85vh] flex flex-col text-card-foreground">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-muted/50">
              <div className="flex items-center gap-2">
                <FileTextIcon className="w-4 h-4 text-primary" />
                <span className="font-bold text-foreground font-mono text-sm">
                  {editArtifactFilename || "Edit Artifact"}
                </span>
              </div>
              <button
                type="button"
                aria-label="Close code modal"
                onClick={() => setIsCodeModalOpen(false)}
                className="text-muted-foreground hover:text-foreground p-1 cursor-pointer"
              >
                <XIcon className="w-5 h-5" />
              </button>
            </div>

            <div className="grow bg-muted overflow-hidden relative flex items-center justify-center">
              {isLoadingCode ? (
                <p className="text-xs text-muted-foreground animate-pulse font-mono">
                  Fetching file content from server...
                </p>
              ) : (
                <MonacoEditor
                  height="100%"
                  width="100%"
                  defaultLanguage="python"
                  value={editCodeText}
                  onChange={(val) => setEditCodeText(val || "")}
                />
              )}
            </div>

            <div className="p-4 border-t border-border flex justify-end gap-2 bg-muted/40 rounded-b-lg">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCodeModalOpen(false)}
                disabled={isSavingCode}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={saveCodeChanges}
                disabled={isSavingCode}
              >
                <SaveIcon className="w-4 h-4 mr-1.5" />
                {isSavingCode ? "Saving..." : "Save"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
