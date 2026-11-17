"use client";

import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import MonacoEditor from "@/components/monaco-editor";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  PlusIcon,
  Trash2Icon,
  FileTextIcon,
  DownloadIcon,
  RefreshCwIcon,
  SparklesIcon,
  Code2Icon,
  CopyIcon,
  CheckIcon,
} from "lucide-react";
import { defaultSuiteFilename } from "@/features/assignments/types";
import { apiClient } from "@/lib/api-client";
import { useAssignmentEditor } from "./assignment-editor-context";
import { AITestAssistantDialog } from "./ai-test-assistant-dialog";
import { ConceptDenylistSection } from "./concept-denylist-section";

interface PythonHelpersPayload {
  filename: string;
  source: string;
  usage_notes: string;
}

export function ScoringRulesSection() {
  const {
    courseId,
    assignmentId,
    description,
    language,
    testFramework,
    scoringItems,
    addScoringItem,
    removeScoringItem,
    updateScoringItemField,
    testSuiteCode,
    updateTestSuiteCode,
    loadingTestSuiteCode,
    syncTestsFromSource,
    setSuccessMessage,
  } = useAssignmentEditor();

  const pytestItems = scoringItems.filter(
    (i) => (i.item_type || "pytest") === "pytest",
  );
  const manualItems = scoringItems.filter((i) => i.item_type === "manual");

  const totalBasePoints = scoringItems.reduce(
    (sum, item) => (item.extra_credit ? sum : sum + (item.points || 0)),
    0,
  );
  const totalExtraCreditPoints = scoringItems.reduce(
    (sum, item) => (item.extra_credit ? sum + (item.points || 0) : sum),
    0,
  );

  const isPython = language === "python";
  const usesSuiteFile = testFramework !== "io";
  const usesComparison = testFramework === "pytest" || testFramework === "io";
  const suiteFilename = defaultSuiteFilename(testFramework);
  const monacoLanguage =
    testFramework === "pytest" ? "python" : testFramework === "gtest" ? "cpp" : "javascript";

  const [isAiAssistantOpen, setIsAiAssistantOpen] = useState(false);
  const [isHelpersOpen, setIsHelpersOpen] = useState(false);
  const [helpersPayload, setHelpersPayload] = useState<PythonHelpersPayload | null>(null);
  const [helpersError, setHelpersError] = useState<string | null>(null);
  const [helpersLoading, setHelpersLoading] = useState(false);
  const [copiedHelpers, setCopiedHelpers] = useState(false);

  const handleViewPythonHelpers = async () => {
    setIsHelpersOpen(true);
    setHelpersError(null);
    if (helpersPayload) return;
    setHelpersLoading(true);
    try {
      const payload = await apiClient.get<PythonHelpersPayload>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/python-helpers`,
      );
      setHelpersPayload(payload);
    } catch (err) {
      setHelpersError(
        err instanceof Error ? err.message : "Could not load Python helpers.",
      );
    } finally {
      setHelpersLoading(false);
    }
  };

  const handleCopyHelpers = async () => {
    if (!helpersPayload?.source) return;
    try {
      await navigator.clipboard.writeText(helpersPayload.source);
      setCopiedHelpers(true);
      setTimeout(() => setCopiedHelpers(false), 2000);
    } catch {
      // Fallback if clipboard API is not available in insecure contexts
    }
  };

  const handleSyncFromCode = async () => {
    const addedCount = await syncTestsFromSource(testSuiteCode);
    if (addedCount === null) return; // The context has surfaced the error; nothing was merged.
    if (addedCount > 0) {
      setSuccessMessage(
        `Synced ${addedCount} new pytest marker(s) into the rubric.`,
      );
    } else {
      setSuccessMessage("All markers in tests.py are already in the rubric.");
    }
  };

  const handleInsertAiTests = async (
    generatedCode: string,
    insertMode: "append" | "replace",
  ) => {
    const nextCode =
      insertMode === "replace"
        ? generatedCode
        : `${testSuiteCode.trimEnd()}\n\n${generatedCode.replace(/^import pytest\s*\n*/i, "").trim()}\n`;
    updateTestSuiteCode(nextCode);
    const added = await syncTestsFromSource(nextCode);
    if (added === null) return;
    setSuccessMessage(
      added > 0
        ? `Inserted AI tests and synced ${added} new rubric criterion(s).`
        : "Inserted AI tests into tests.py.",
    );
  };

  const handleDownload = () => {
    const blob = new Blob([testSuiteCode], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = suiteFilename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* 1. Test suite first */}
      {usesSuiteFile ? (
        <Card size="sm" className="gap-1.5 py-3">
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 px-4 py-0">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileTextIcon className="h-4 w-4 text-primary" />
              {suiteFilename}
            </CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              {isPython && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => void handleViewPythonHelpers()}
                  >
                    <Code2Icon className="mr-1.5 h-4 w-4" />
                    View Python helpers
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsAiAssistantOpen(true)}
                  >
                    <SparklesIcon className="mr-1.5 h-4 w-4 text-primary" />
                    Tests with AI
                  </Button>
                </>
              )}
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <DownloadIcon className="mr-1.5 h-4 w-4" />
                Download
              </Button>
            </div>
          </CardHeader>
          <CardContent className="px-4 py-0">
            <div className="h-[420px] overflow-hidden rounded-lg border border-border bg-card">
              {loadingTestSuiteCode ? (
                <div className="flex h-full items-center justify-center font-mono text-xs text-muted-foreground animate-pulse">
                  Loading {suiteFilename}…
                </div>
              ) : (
                <MonacoEditor
                  height="100%"
                  width="100%"
                  defaultLanguage={monacoLanguage}
                  language={monacoLanguage}
                  value={testSuiteCode}
                  onChange={(val) => updateTestSuiteCode(val || "")}
                />
              )}
            </div>
          </CardContent>
        </Card>
      ) : null}
      <Dialog open={isHelpersOpen} onOpenChange={setIsHelpersOpen}>
        <DialogContent className="flex h-[min(88vh,54rem)] w-[min(96vw,72rem)] max-w-none flex-col gap-3 overflow-hidden p-6 sm:max-w-none">
          <DialogHeader className="shrink-0 flex flex-row items-center justify-between gap-4 pr-8">
            <div className="flex items-center gap-2">
              <Code2Icon className="h-4 w-4 text-primary" />
              <DialogTitle className="text-base font-semibold">
                {helpersPayload?.filename ?? "python_autograder_helpers.py"}
              </DialogTitle>
              <DialogDescription className="sr-only">
                Injected Python helper utilities
              </DialogDescription>
            </div>
            {helpersPayload?.source && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => void handleCopyHelpers()}
                aria-label="Copy helper source"
              >
                {copiedHelpers ? (
                  <>
                    <CheckIcon className="mr-1.5 h-3.5 w-3.5 text-emerald-500" />
                    Copied
                  </>
                ) : (
                  <>
                    <CopyIcon className="mr-1.5 h-3.5 w-3.5" />
                    Copy
                  </>
                )}
              </Button>
            )}
          </DialogHeader>
          <div className="min-h-0 flex-1 overflow-hidden rounded-lg border border-border bg-card">
            {helpersLoading ? (
              <div className="flex h-full items-center justify-center font-mono text-xs text-muted-foreground animate-pulse">
                Loading helper source…
              </div>
            ) : helpersError ? (
              <div className="flex h-full items-center justify-center px-4 text-sm text-destructive">
                {helpersError}
              </div>
            ) : (
              <MonacoEditor
                height="100%"
                width="100%"
                defaultLanguage="python"
                value={helpersPayload?.source ?? ""}
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                }}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* 2. Automated tests */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 px-4 py-0">
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle className="text-base">Automated tests</CardTitle>
            <span className="rounded-md bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">
              {totalBasePoints} pts
              {totalExtraCreditPoints > 0
                ? ` · +${totalExtraCreditPoints} extra credit`
                : ""}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {isPython && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => void handleSyncFromCode()}
              >
                <RefreshCwIcon className="mr-1.5 h-4 w-4" />
                Sync from tests
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => addScoringItem("pytest")}
            >
              <PlusIcon className="mr-1 h-4 w-4" />
              Add
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-2 px-4 py-0">
          {pytestItems.length > 0 && (
            <div className="hidden grid-cols-[minmax(7rem,9rem)_minmax(0,1fr)_4.5rem_5.5rem_4rem_2rem] gap-2 px-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground md:grid">
              <span>{testFramework === "pytest" ? "Marker" : "Key"}</span>
              <span>Description</span>
              <span>Points</span>
              <span className="text-center">Extra credit</span>
              <span className="text-center">Private</span>
              <span className="sr-only">Remove</span>
            </div>
          )}

          <div className="space-y-2">
            {pytestItems.map((item) => {
              const rowId = item.id || item.key;
              return (
                <div
                  key={rowId}
                  className="rounded-lg border border-border bg-card p-2 text-sm"
                >
                  <div className="grid grid-cols-1 items-center gap-2 md:grid-cols-[minmax(7rem,9rem)_minmax(0,1fr)_4.5rem_5.5rem_4rem_2rem]">
                    <div className="relative flex items-center">
                      <span className="pointer-events-none absolute left-2 select-none font-mono text-[10px] font-bold text-muted-foreground">
                        ag_
                      </span>
                      <Input
                        id={`scoring-key-${rowId}`}
                        aria-label={testFramework === "pytest" ? "Pytest marker key" : "Test key"}
                        value={item.key}
                        onChange={(e) =>
                          updateScoringItemField(rowId, "key", e.target.value)
                        }
                        className="h-8 pl-7 font-mono text-xs"
                      />
                    </div>
                    <Input
                      id={`scoring-label-${rowId}`}
                      aria-label="Criterion description"
                      value={item.label}
                      onChange={(e) =>
                        updateScoringItemField(rowId, "label", e.target.value)
                      }
                      placeholder="Description"
                      className="h-8"
                    />
                    <Input
                      id={`scoring-points-${rowId}`}
                      aria-label="Points"
                      type="number"
                      min={0}
                      value={item.points}
                      onChange={(e) =>
                        updateScoringItemField(
                          rowId,
                          "points",
                          parseInt(e.target.value, 10) || 0,
                        )
                      }
                      className="h-8 font-mono"
                    />
                    <div className="flex h-8 items-center justify-center">
                      <input
                        id={`scoring-ec-${rowId}`}
                        type="checkbox"
                        aria-label="Extra credit"
                        checked={Boolean(item.extra_credit)}
                        onChange={(e) =>
                          updateScoringItemField(
                            rowId,
                            "extra_credit",
                            e.target.checked,
                          )
                        }
                        className="h-3.5 w-3.5 cursor-pointer rounded border-input text-primary focus:ring-ring"
                      />
                    </div>
                    <div className="flex h-8 items-center justify-center">
                      <input
                        id={`scoring-private-${rowId}`}
                        type="checkbox"
                        aria-label="Private"
                        checked={Boolean(item.is_private)}
                        onChange={(e) =>
                          updateScoringItemField(
                            rowId,
                            "is_private",
                            e.target.checked,
                          )
                        }
                        className="h-3.5 w-3.5 cursor-pointer rounded border-input text-primary focus:ring-ring"
                      />
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      aria-label="Remove criterion"
                      onClick={() => removeScoringItem(rowId)}
                    >
                      <Trash2Icon className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>

                  {usesComparison && (
                  <div className="mt-2 flex flex-wrap items-center gap-2.5 border-t border-border pt-2 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-foreground text-[11px]">Mode:</span>
                      <select
                        id={`scoring-mode-${rowId}`}
                        aria-label="Comparison mode"
                        value={item.comparison_mode || "normalized"}
                        onChange={(e) =>
                          updateScoringItemField(
                            rowId,
                            "comparison_mode",
                            e.target.value,
                          )
                        }
                        className="h-7 rounded border border-input bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                      >
                        <option value="normalized">Normalized (default)</option>
                        <option value="exact">Exact string</option>
                        <option value="numeric_tolerance">Numeric (±ε)</option>
                        <option value="regex">Regex pattern</option>
                      </select>
                    </div>

                    {item.comparison_mode === "numeric_tolerance" && (
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] text-muted-foreground">Tolerance (ε):</span>
                        <Input
                          id={`scoring-tol-${rowId}`}
                          aria-label="Tolerance"
                          type="number"
                          step="any"
                          min="0"
                          placeholder="0.0001"
                          value={item.tolerance !== null && item.tolerance !== undefined ? item.tolerance : ""}
                          onChange={(e) => {
                            const val = e.target.value.trim() === "" ? null : parseFloat(e.target.value);
                            updateScoringItemField(
                              rowId,
                              "tolerance",
                              val !== null && !isNaN(val) ? val : null,
                            );
                          }}
                          className="h-7 w-24 font-mono text-xs"
                        />
                      </div>
                    )}

                    {testFramework === "pytest" &&
                      ((item.inputs && item.inputs.length > 0) ||
                      (item.outputs && item.outputs.length > 0)) && (
                      <div className="flex flex-wrap items-center gap-2 pl-2 border-l border-border">
                        <span className="flex items-center gap-1 font-semibold text-foreground">
                          <FileTextIcon className="h-3.5 w-3.5 text-primary" />
                          I/O
                        </span>
                        {item.inputs && item.inputs.length > 0 && (
                          <span className="rounded border border-info/30 bg-info/10 px-2 py-0.5 font-mono text-info">
                            in: {item.inputs.join(", ")}
                          </span>
                        )}
                        {item.outputs && item.outputs.length > 0 && (
                          <span className="rounded border border-success/30 bg-success/10 px-2 py-0.5 font-mono text-success">
                            out: {item.outputs.join(", ")}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  )}

                  {testFramework === "io" && (
                    <IoCasesEditor
                      inputs={item.inputs || []}
                      outputs={item.outputs || []}
                      onChange={(inputs, outputs) => {
                        updateScoringItemField(rowId, "inputs", inputs);
                        updateScoringItemField(rowId, "outputs", outputs);
                      }}
                    />
                  )}
                </div>
              );
            })}

            {pytestItems.length === 0 && (
              <p className="rounded-lg border border-dashed border-border px-3 py-3 text-center text-xs text-muted-foreground">
                {isPython ? "None yet. Sync from tests or add." : "None yet. Add a test."}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 3. Manual criteria */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 px-4 py-0">
          <CardTitle className="text-base">Manual criteria</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => addScoringItem("manual")}
          >
            <PlusIcon className="mr-1 h-4 w-4" />
            Add
          </Button>
        </CardHeader>
        <CardContent className="space-y-2 px-4 py-0">
          {manualItems.length > 0 && (
            <>
              <div className="hidden grid-cols-[minmax(0,1fr)_4.5rem_5.5rem_2rem] gap-2 px-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground md:grid">
                <span>Label</span>
                <span>Points</span>
                <span className="text-center">Extra credit</span>
                <span className="sr-only">Remove</span>
              </div>
              {manualItems.map((item) => {
                const rowId = item.id || item.key;
                return (
                  <div
                    key={rowId}
                    className="space-y-2 rounded-lg border border-border bg-card p-2.5"
                  >
                    <div className="grid grid-cols-1 items-center gap-2 md:grid-cols-[minmax(0,1fr)_4.5rem_5.5rem_2rem]">
                      <Input
                        id={`manual-label-${rowId}`}
                        aria-label="Manual criterion label"
                        value={item.label}
                        onChange={(e) =>
                          updateScoringItemField(rowId, "label", e.target.value)
                        }
                        placeholder="e.g. Code style"
                        className="h-8"
                      />
                      <Input
                        id={`manual-points-${rowId}`}
                        aria-label="Points"
                        type="number"
                        min={0}
                        value={item.points}
                        onChange={(e) =>
                          updateScoringItemField(
                            rowId,
                            "points",
                            parseInt(e.target.value, 10) || 0,
                          )
                        }
                        className="h-8 font-mono"
                      />
                      <div className="flex h-8 items-center justify-center">
                        <input
                          id={`manual-ec-${rowId}`}
                          type="checkbox"
                          aria-label="Extra credit"
                          checked={Boolean(item.extra_credit)}
                          onChange={(e) =>
                            updateScoringItemField(
                              rowId,
                              "extra_credit",
                              e.target.checked,
                            )
                          }
                          className="h-3.5 w-3.5 cursor-pointer rounded border-input text-primary focus:ring-ring"
                        />
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        aria-label="Remove manual criterion"
                        onClick={() => removeScoringItem(rowId)}
                      >
                        <Trash2Icon className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>

                    <ManualCommentTemplatesManager
                      templates={item.comment_templates || []}
                      criterionLabel={item.label}
                      onChange={(templates) =>
                        updateScoringItemField(rowId, "comment_templates", templates)
                      }
                    />
                  </div>
                );
              })}
            </>
          )}
        </CardContent>
      </Card>

      <ConceptDenylistSection />

      {isPython && (
        <AITestAssistantDialog
          isOpen={isAiAssistantOpen}
          onOpenChange={setIsAiAssistantOpen}
          courseId={courseId}
          assignmentId={assignmentId}
          assignmentDescription={description}
          currentTestCode={testSuiteCode}
          onInsertTests={handleInsertAiTests}
        />
      )}
    </div>
  );
}

interface IoCasesEditorProps {
  inputs: string[];
  outputs: string[];
  onChange: (inputs: string[], outputs: string[]) => void;
}

/** Editable stdin / expected-stdout case rows for the `io` framework. */
function IoCasesEditor({ inputs, outputs, onChange }: IoCasesEditorProps) {
  const count = Math.max(inputs.length, outputs.length);
  const pad = (arr: string[]) => Array.from({ length: count }, (_, i) => arr[i] ?? "");
  const setCase = (idx: number, field: "in" | "out", value: string) => {
    const nextIn = pad(inputs);
    const nextOut = pad(outputs);
    (field === "in" ? nextIn : nextOut)[idx] = value;
    onChange(nextIn, nextOut);
  };
  const removeCase = (idx: number) =>
    onChange(pad(inputs).filter((_, i) => i !== idx), pad(outputs).filter((_, i) => i !== idx));

  return (
    <div className="mt-2 space-y-1.5 border-t border-border pt-2 text-xs">
      <div className="flex items-center justify-between text-[11px] font-medium text-muted-foreground">
        <span>I/O cases ({count})</span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-7 px-2 text-xs"
          onClick={() => onChange([...pad(inputs), ""], [...pad(outputs), ""])}
        >
          <PlusIcon className="mr-1 h-3 w-3" />
          Add case
        </Button>
      </div>
      {pad(inputs).map((input, idx) => (
        <div key={idx} className="grid grid-cols-1 items-start gap-2 md:grid-cols-[1fr_1fr_2rem]">
          <Textarea
            aria-label={`Case ${idx + 1} input`}
            placeholder="stdin"
            rows={2}
            value={input}
            onChange={(e) => setCase(idx, "in", e.target.value)}
            className="font-mono text-xs"
          />
          <Textarea
            aria-label={`Case ${idx + 1} expected output`}
            placeholder="expected stdout"
            rows={2}
            value={pad(outputs)[idx]}
            onChange={(e) => setCase(idx, "out", e.target.value)}
            className="font-mono text-xs"
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            aria-label={`Remove case ${idx + 1}`}
            onClick={() => removeCase(idx)}
          >
            <Trash2Icon className="h-4 w-4 text-destructive" />
          </Button>
        </div>
      ))}
    </div>
  );
}

interface ManualCommentTemplatesManagerProps {
  templates: string[];
  onChange: (templates: string[]) => void;
  criterionLabel: string;
}

function ManualCommentTemplatesManager({
  templates,
  onChange,
  criterionLabel,
}: ManualCommentTemplatesManagerProps) {
  const [newText, setNewText] = useState("");

  const handleAdd = () => {
    const trimmed = newText.trim();
    if (!trimmed) return;
    if (templates.includes(trimmed)) {
      setNewText("");
      return;
    }
    onChange([...templates, trimmed]);
    setNewText("");
  };

  const handleRemove = (index: number) => {
    onChange(templates.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t border-border/50 pt-2 text-xs space-y-1.5">
      <div className="flex items-center justify-between text-[11px] font-medium text-muted-foreground">
        <span>Reusable comment snippets ({templates.length})</span>
      </div>
      {templates.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-0.5">
          {templates.map((tpl, i) => (
            <span
              key={`${tpl}-${i}`}
              className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-0.5 text-[11px] text-secondary-foreground"
            >
              <span className="truncate max-w-[20rem]">{tpl}</span>
              <button
                type="button"
                aria-label={`Remove snippet "${tpl}"`}
                onClick={() => handleRemove(i)}
                className="ml-0.5 text-muted-foreground hover:text-destructive cursor-pointer"
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex items-center gap-1.5 pt-0.5">
        <Input
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAdd();
            }
          }}
          placeholder={`Add snippet for ${criterionLabel || "criterion"}...`}
          className="h-7 text-xs"
        />
        <Button
          type="button"
          size="sm"
          variant="secondary"
          onClick={handleAdd}
          disabled={!newText.trim()}
          aria-label="Add snippet"
          className="h-7 px-2.5 text-xs shrink-0"
        >
          <PlusIcon className="mr-1 h-3 w-3" />
          Add
        </Button>
      </div>
    </div>
  );
}
