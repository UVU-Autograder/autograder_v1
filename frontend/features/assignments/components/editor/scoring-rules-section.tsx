"use client";

import React, { useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import MonacoEditor from "@/components/monaco-editor";
import {
  PlusIcon,
  Trash2Icon,
  FileTextIcon,
  DownloadIcon,
  RefreshCwIcon,
  SparklesIcon,
  AlertCircleIcon,
} from "lucide-react";
import { pytestMarkerForKey } from "@/features/assignments/types";
import { useAssignmentEditor } from "./assignment-editor-context";
import { AITestAssistantDialog } from "./ai-test-assistant-dialog";
import { ConceptDenylistSection } from "./concept-denylist-section";

const MARKER_RE = /@(?:pytest\.)?(?:mark\.)?ag_([a-zA-Z0-9_]+)/g;

function extractMarkerKeys(sourceCode: string): string[] {
  const keys = new Set<string>();
  for (const match of sourceCode.matchAll(MARKER_RE)) {
    if (match[1]) keys.add(match[1]);
  }
  return [...keys];
}

export function ScoringRulesSection() {
  const {
    courseId,
    assignmentId,
    description,
    scoringItems,
    addScoringItem,
    removeScoringItem,
    updateScoringItemField,
    testSuiteCode,
    updateTestSuiteCode,
    loadingTestSuiteCode,
    syncMarkersFromTestSuite,
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

  const { missingFromRubric, orphanInRubric } = useMemo(() => {
    const codeKeys = extractMarkerKeys(testSuiteCode);
    const rubricKeys = new Set(pytestItems.map((i) => i.key).filter(Boolean));
    return {
      missingFromRubric: codeKeys.filter((k) => !rubricKeys.has(k)),
      orphanInRubric: pytestItems
        .map((i) => i.key)
        .filter((k) => k && !codeKeys.includes(k)),
    };
  }, [testSuiteCode, pytestItems]);

  const [isAiAssistantOpen, setIsAiAssistantOpen] = useState(false);

  const handleSyncFromCode = () => {
    const addedCount = syncMarkersFromTestSuite(testSuiteCode);
    if (addedCount > 0) {
      setSuccessMessage(
        `Synced ${addedCount} new pytest marker(s) into the rubric.`,
      );
    } else {
      setSuccessMessage("All markers in tests.py are already in the rubric.");
    }
  };

  const handleInsertAiTests = (
    generatedCode: string,
    insertMode: "append" | "replace",
  ) => {
    const nextCode =
      insertMode === "replace"
        ? generatedCode
        : `${testSuiteCode.trimEnd()}\n\n${generatedCode.replace(/^import pytest\s*\n*/i, "").trim()}\n`;
    updateTestSuiteCode(nextCode);
    const added = syncMarkersFromTestSuite(nextCode);
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
    a.download = "tests.py";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* 1. Test suite first */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 px-4 py-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <FileTextIcon className="h-4 w-4 text-primary" />
            tests.py
          </CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAiAssistantOpen(true)}
            >
              <SparklesIcon className="mr-1.5 h-4 w-4 text-primary" />
              Tests with AI
            </Button>
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
                Loading tests.py…
              </div>
            ) : (
              <MonacoEditor
                height="100%"
                width="100%"
                defaultLanguage="python"
                value={testSuiteCode}
                onChange={(val) => updateTestSuiteCode(val || "")}
              />
            )}
          </div>
        </CardContent>
      </Card>

      {/* 2. Autograded criteria */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 px-4 py-0">
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle className="text-base">Autograded criteria</CardTitle>
            <span className="rounded-md bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">
              {totalBasePoints} pts
              {totalExtraCreditPoints > 0
                ? ` · +${totalExtraCreditPoints} extra credit`
                : ""}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleSyncFromCode}>
              <RefreshCwIcon className="mr-1.5 h-4 w-4" />
              Sync from tests
            </Button>
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
          {(missingFromRubric.length > 0 || orphanInRubric.length > 0) && (
            <div className="flex flex-wrap items-start gap-2 rounded-md border border-border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
              <AlertCircleIcon className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <div className="min-w-0 flex-1 space-y-0.5">
                {missingFromRubric.length > 0 && (
                  <p>
                    <span className="font-medium text-foreground">
                      {missingFromRubric.length}
                    </span>{" "}
                    marker
                    {missingFromRubric.length === 1 ? "" : "s"} in tests.py not
                    in the rubric
                    <span className="text-muted-foreground">
                      {" "}
                      ({missingFromRubric.map((k) => pytestMarkerForKey(k)).join(", ")})
                    </span>
                    .
                  </p>
                )}
                {orphanInRubric.length > 0 && (
                  <p>
                    <span className="font-medium text-foreground">
                      {orphanInRubric.length}
                    </span>{" "}
                    rubric key
                    {orphanInRubric.length === 1 ? "" : "s"} missing from
                    tests.py
                    <span className="text-muted-foreground">
                      {" "}
                      ({orphanInRubric.map((k) => pytestMarkerForKey(k)).join(", ")})
                    </span>
                    .
                  </p>
                )}
              </div>
            </div>
          )}

          {pytestItems.length > 0 && (
            <div className="hidden grid-cols-[minmax(7rem,9rem)_minmax(0,1fr)_4.5rem_5.5rem_4rem_2rem] gap-2 px-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground md:grid">
              <span>Marker</span>
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
              const isOrphan = Boolean(item.key) && orphanInRubric.includes(item.key);
              return (
                <div
                  key={rowId}
                  className={`rounded-lg border bg-card p-2 text-sm ${
                    isOrphan
                      ? "border-amber-500/40 bg-amber-500/5"
                      : "border-border"
                  }`}
                >
                  <div className="grid grid-cols-1 items-center gap-2 md:grid-cols-[minmax(7rem,9rem)_minmax(0,1fr)_4.5rem_5.5rem_4rem_2rem]">
                    <div className="relative flex items-center">
                      <span className="pointer-events-none absolute left-2 select-none font-mono text-[10px] font-bold text-muted-foreground">
                        ag_
                      </span>
                      <Input
                        id={`scoring-key-${rowId}`}
                        aria-label="Pytest marker key"
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

                  {((item.inputs && item.inputs.length > 0) ||
                    (item.outputs && item.outputs.length > 0)) && (
                    <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-border pt-2 text-xs text-muted-foreground">
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
              );
            })}

            {pytestItems.length === 0 && (
              <p className="rounded-lg border border-dashed border-border px-3 py-3 text-center text-xs text-muted-foreground">
                None yet. Sync from tests or add.
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
                    className="grid grid-cols-1 items-center gap-2 rounded-lg border border-border bg-card p-2 md:grid-cols-[minmax(0,1fr)_4.5rem_5.5rem_2rem]"
                  >
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
                );
              })}
            </>
          )}
        </CardContent>
      </Card>

      <ConceptDenylistSection />

      <AITestAssistantDialog
        isOpen={isAiAssistantOpen}
        onOpenChange={setIsAiAssistantOpen}
        courseId={courseId}
        assignmentId={assignmentId}
        assignmentDescription={description}
        currentTestCode={testSuiteCode}
        onInsertTests={handleInsertAiTests}
      />
    </div>
  );
}
