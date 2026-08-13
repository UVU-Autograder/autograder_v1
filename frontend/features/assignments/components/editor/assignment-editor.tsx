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
} from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";
import { MetadataSection } from "./metadata-section";
import { ScoringRulesSection } from "./scoring-rules-section";
import { ConceptWhitelistSection } from "./concept-whitelist-section";
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
      <div className="flex items-center justify-center min-h-[400px] text-muted-foreground font-mono text-sm animate-pulse">
        Loading assignment setup configuration...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-border pb-4">
        <div className="space-y-1">
          <BackLink href={`/staff/courses/${courseId}/assignments`}>
            Back to course details
          </BackLink>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              {title || assignmentId}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {saveSuccess && (
            <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
              <CheckCircle2Icon className="w-4 h-4" /> Saved successfully
            </span>
          )}
          {dirty && (
            <span className="text-xs text-amber-600 dark:text-amber-400 font-medium">
              Unsaved changes
            </span>
          )}

          <Button
            variant="outline"
            onClick={handleCopyStudentLink}
            className="flex items-center gap-1.5 cursor-pointer"
          >
            {copiedLink ? (
              <>
                <CheckIcon className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <CopyIcon className="w-4 h-4" />
                <span>Copy Student Link</span>
              </>
            )}
          </Button>

          <Button
            variant="outline"
            onClick={handleDelete}
            className="flex items-center gap-1.5 text-destructive border-destructive/30 hover:bg-destructive/10 cursor-pointer"
          >
            <Trash2Icon className="w-4 h-4" />
            <span>Delete Assignment</span>
          </Button>

          <Button variant="default" onClick={handleSave} disabled={saving}>
            <SaveIcon className="w-4 h-4 mr-1.5" />
            {saving ? "Saving..." : "Save Setup"}
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {errorMessage && (
        <div className="flex items-start gap-2 p-3 bg-destructive/10 text-destructive rounded-lg text-sm border border-destructive/30 whitespace-pre-line">
          <ShieldAlertIcon className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Setup Error</div>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="flex items-center gap-2 p-3 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-lg text-sm border border-emerald-500/30">
          <CheckCircle2Icon className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Tabs Navigation */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-4 max-w-2xl bg-muted p-1 rounded-lg">
          <TabsTrigger value="metadata">General & Files</TabsTrigger>
          <TabsTrigger value="rubrics">Test Suite & Rubric</TabsTrigger>
          <TabsTrigger value="whitelist">Concepts</TabsTrigger>
          <TabsTrigger value="model_solution">Model Solution</TabsTrigger>
        </TabsList>

        <TabsContent value="metadata">
          <MetadataSection />
        </TabsContent>

        <TabsContent value="rubrics">
          <ScoringRulesSection />
        </TabsContent>

        <TabsContent value="whitelist">
          <ConceptWhitelistSection />
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
                <p className="text-xs text-slate-400 animate-pulse font-mono">
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

            <div className="p-4 border-t border-slate-200 flex justify-end gap-2 bg-slate-50 rounded-b-lg">
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
                {isSavingCode ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
