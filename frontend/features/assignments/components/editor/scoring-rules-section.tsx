"use client";

import React, { useState, useMemo } from "react";
import {
  Card,
  CardContent,
  CardDescription,
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
  SaveIcon,
  RefreshCwIcon,
  CheckCircle2Icon,
  SparklesIcon,
  AlertTriangleIcon,
  CodeIcon,
} from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";
import { AITestAssistantDialog } from "./ai-test-assistant-dialog";

export function ScoringRulesSection() {
  const {
    courseId,
    assignmentId,
    scoringItems,
    addScoringItem,
    removeScoringItem,
    updateScoringItemField,
    autoGenerateKeyFromLabel,
    testSuiteCode,
    updateTestSuiteCode,
    loadingTestSuiteCode,
    saving,
    saveSuccess,
    syncMarkersFromTestSuite,
    handleSave,
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

  const [isAiAssistantOpen, setIsAiAssistantOpen] = useState(false);

  // Live marker analysis comparing tests.py vs rubric items
  const codeMarkerKeys = useMemo(() => {
    const keys = new Set<string>();
    const regex = /@pytest\.mark\.ag_([a-zA-Z0-9_]+)/g;
    let match: RegExpExecArray | null;
    while ((match = regex.exec(testSuiteCode)) !== null) {
      if (match[1]) keys.add(match[1]);
    }
    return keys;
  }, [testSuiteCode]);

  const unmappedCodeMarkers = useMemo(() => {
    const rubricKeys = new Set(pytestItems.map((i) => i.key));
    return Array.from(codeMarkerKeys).filter((k) => !rubricKeys.has(k));
  }, [codeMarkerKeys, pytestItems]);

  const handleSyncFromCode = () => {
    const addedCount = syncMarkersFromTestSuite(testSuiteCode);
    if (addedCount > 0) {
      setSuccessMessage(
        `Synced ${addedCount} new pytest test marker(s) into rubric!`,
      );
    } else {
      setSuccessMessage(
        "All pytest test markers in code are already present in rubric.",
      );
    }
  };

  const handleInsertStubTest = (key: string, label: string) => {
    const cleanKey = key.replace(/[^a-zA-Z0-9_]/g, "_") || "check";
    const stub = `\n\n@pytest.mark.ag_${cleanKey}\ndef test_${cleanKey}(monkeypatch, capsys):\n    """${label || cleanKey}"""\n    EXPECTED_INPUT = []\n    EXPECTED_OUTPUT = ""\n    assert True\n`;
    updateTestSuiteCode(`${testSuiteCode.trimEnd()}${stub}`);
    setSuccessMessage(`Inserted @pytest.mark.ag_${cleanKey} stub into tests.py`);
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
        ? `Inserted AI test suite and synced ${added} new rubric criterion(s).`
        : "Inserted AI test suite into tests.py editor.",
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
      {/* Autograded Pytest Criteria */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Autograded Test Criteria</CardTitle>
            <CardDescription>
              Each description/label acts as the test group header for asserts
              under{" "}
              <code className="font-mono bg-muted px-1 py-0.5 rounded text-foreground">
                tests.py
              </code>
              . Base Total:{" "}
              <strong className="text-foreground font-mono">
                {totalBasePoints} pts
              </strong>
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsAiAssistantOpen(true)}
            >
              <SparklesIcon className="w-4 h-4 mr-1.5 text-primary" /> AI Test
              Assistant
            </Button>
            <Button variant="outline" size="sm" onClick={handleSyncFromCode}>
              <RefreshCwIcon className="w-4 h-4 mr-1.5" /> Sync Markers from
              Code
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => addScoringItem("pytest")}
            >
              <PlusIcon className="w-4 h-4 mr-1" /> Add Pytest Item
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {unmappedCodeMarkers.length > 0 && (
            <div className="mb-4 p-3 rounded-lg bg-warning/10 border border-warning/30 flex flex-wrap items-center justify-between gap-2 text-xs">
              <span className="text-warning font-medium flex items-center gap-1.5">
                <AlertTriangleIcon className="w-4 h-4 shrink-0" />
                Found {unmappedCodeMarkers.length} marker(s) in{" "}
                <code className="font-mono">tests.py</code> not yet in the
                rubric:{" "}
                <code className="font-mono font-bold">
                  {unmappedCodeMarkers.map((m) => `ag_${m}`).join(", ")}
                </code>
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={handleSyncFromCode}
                className="h-7 text-xs"
              >
                <RefreshCwIcon className="w-3.5 h-3.5 mr-1" /> Add to Rubric
              </Button>
            </div>
          )}

          <div className="space-y-3">
            {pytestItems.map((item) => {
              const hasMarkerInCode = codeMarkerKeys.has(item.key);
              return (
                <div
                  key={item.id || item.key}
                  className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3 bg-card rounded-lg border border-border items-center text-sm"
                >
                  {/* Key / Slug */}
                  <div className="md:col-span-4 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-muted-foreground uppercase">
                        Key / Pytest Marker
                      </span>
                      <button
                        type="button"
                        onClick={() =>
                          autoGenerateKeyFromLabel(item.id || item.key)
                        }
                        className="text-xs flex items-center gap-1 text-primary font-semibold hover:underline cursor-pointer"
                        title="Auto-generate key from description"
                      >
                        Auto-generate key
                      </button>
                    </div>
                    <div className="relative flex items-center">
                      <span className="absolute left-2.5 text-xs font-mono font-bold text-muted-foreground select-none pointer-events-none">
                        ag_
                      </span>
                      <Input
                        value={item.key}
                        onChange={(e) =>
                          updateScoringItemField(
                            item.id || item.key,
                            "key",
                            e.target.value,
                          )
                        }
                        className="font-mono text-xs pl-8"
                      />
                    </div>
                  </div>

                  {/* Label / Description Header */}
                  <div className="md:col-span-5 space-y-1">
                    <span className="text-xs font-semibold text-muted-foreground uppercase">
                      Description
                    </span>
                    <Input
                      value={item.label}
                      onChange={(e) =>
                        updateScoringItemField(
                          item.id || item.key,
                          "label",
                          e.target.value,
                        )
                      }
                      placeholder="e.g. Basic Calculator Operations"
                    />
                  </div>

                  {/* Points */}
                  <div className="md:col-span-2 space-y-1">
                    <span className="text-xs font-semibold text-muted-foreground uppercase">
                      Points
                    </span>
                    <Input
                      type="number"
                      value={item.points}
                      onChange={(e) =>
                        updateScoringItemField(
                          item.id || item.key,
                          "points",
                          parseInt(e.target.value, 10) || 0,
                        )
                      }
                      className="font-mono"
                    />
                  </div>

                  {/* Delete */}
                  <div className="md:col-span-1 flex justify-end">
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label="Remove test item"
                      onClick={() => removeScoringItem(item.id || item.key)}
                    >
                      <Trash2Icon className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>

                  {/* Expected I/O Preview & Marker Link Status */}
                  <div className="md:col-span-12 mt-1 pt-2 border-t border-border flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="font-semibold text-foreground flex items-center gap-1">
                        <FileTextIcon className="w-3.5 h-3.5 text-primary" />
                        Parsed Expected I/O:
                      </span>
                      {(item.inputs && item.inputs.length > 0) ||
                      (item.outputs && item.outputs.length > 0) ? (
                        <div className="flex flex-wrap items-center gap-2">
                          {item.inputs && item.inputs.length > 0 && (
                            <span
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-info/10 text-info border border-info/30"
                              title="Expected Input"
                            >
                              <strong className="mr-1 font-sans font-semibold">
                                Input:
                              </strong>{" "}
                              {item.inputs.join(", ")}
                            </span>
                          )}
                          {item.outputs && item.outputs.length > 0 && (
                            <span
                              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono bg-success/10 text-success border border-success/30"
                              title="Expected Output"
                            >
                              <strong className="mr-1 font-sans font-semibold">
                                Output:
                              </strong>{" "}
                              {item.outputs.join(", ")}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground italic">
                          No EXPECTED_INPUT or EXPECTED_OUTPUT in ag_{item.key}.
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {hasMarkerInCode ? (
                        <span className="inline-flex items-center gap-1 text-success font-medium">
                          <CheckCircle2Icon className="w-3.5 h-3.5" /> Linked in
                          tests.py
                        </span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center gap-1 text-warning font-medium">
                            <AlertTriangleIcon className="w-3.5 h-3.5" /> Missing{" "}
                            <code className="font-mono">
                              @pytest.mark.ag_{item.key}
                            </code>{" "}
                            in tests.py
                          </span>
                          <button
                            type="button"
                            onClick={() =>
                              handleInsertStubTest(item.key, item.label)
                            }
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded border border-primary/30 bg-primary/10 text-primary font-semibold hover:bg-primary/20 cursor-pointer"
                          >
                            <CodeIcon className="w-3 h-3" /> Insert Stub Test
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {pytestItems.length === 0 && (
              <p className="text-xs text-muted-foreground italic p-4 text-center border border-dashed border-border rounded-lg">
                No autograded pytest criteria configured. Click &quot;Add Pytest
                Item&quot; or &quot;Sync Markers from Code&quot;.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Manual Rubric Criteria */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Manual Rubric Criteria (Optional)</CardTitle>
            <CardDescription>
              Criteria evaluated manually by staff (e.g. code style, structure).
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => addScoringItem("manual")}
          >
            <PlusIcon className="w-4 h-4 mr-1" /> Add Manual Item
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {manualItems.map((item) => (
              <div
                key={item.id || item.key}
                className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3 bg-card rounded-lg border border-border items-center text-sm text-card-foreground"
              >
                {/* Label / Description Header */}
                <div className="md:col-span-9 space-y-1">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">
                    Criterion Label
                  </span>
                  <Input
                    value={item.label}
                    onChange={(e) =>
                      updateScoringItemField(
                        item.id || item.key,
                        "label",
                        e.target.value,
                      )
                    }
                    placeholder="e.g. Code Formatting & Comments"
                  />
                </div>

                {/* Points */}
                <div className="md:col-span-2 space-y-1">
                  <span className="text-xs font-semibold text-muted-foreground uppercase">
                    Points
                  </span>
                  <Input
                    type="number"
                    value={item.points}
                    onChange={(e) =>
                      updateScoringItemField(
                        item.id || item.key,
                        "points",
                        parseInt(e.target.value, 10) || 0,
                      )
                    }
                    className="font-mono"
                  />
                </div>

                {/* Delete */}
                <div className="md:col-span-1 flex justify-end">
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label="Remove manual rubric item"
                    onClick={() => removeScoringItem(item.id || item.key)}
                  >
                    <Trash2Icon className="w-4 h-4 text-destructive" />
                  </Button>
                </div>
              </div>
            ))}

            {manualItems.length === 0 && (
              <p className="text-xs text-muted-foreground italic p-4 text-center border border-dashed border-border rounded-lg">
                No manual rubric items configured.
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Integrated tests.py Code Editor */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileTextIcon className="w-5 h-5 text-primary" />
              <span>Assignment Test Suite</span>
            </CardTitle>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {saveSuccess && (
              <span className="text-xs text-success font-semibold flex items-center gap-1">
                <CheckCircle2Icon className="w-4 h-4" /> Saved tests.py & rubric
              </span>
            )}
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsAiAssistantOpen(true)}
            >
              <SparklesIcon className="w-4 h-4 mr-1.5 text-primary" /> AI
              Generate / Refine Tests
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <DownloadIcon className="w-4 h-4 mr-1.5" /> Download tests.py
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={saving}
            >
              <SaveIcon className="w-4 h-4 mr-1.5" />
              {saving ? "Saving..." : "Save Test Suite & Rubric"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[520px] rounded-lg border border-border overflow-hidden bg-card">
            {loadingTestSuiteCode ? (
              <div className="flex items-center justify-center h-full text-xs text-muted-foreground font-mono animate-pulse">
                Fetching tests.py source code from server...
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

      <AITestAssistantDialog
        isOpen={isAiAssistantOpen}
        onOpenChange={setIsAiAssistantOpen}
        courseId={courseId}
        assignmentId={assignmentId}
        currentTestCode={testSuiteCode}
        onInsertTests={handleInsertAiTests}
      />
    </div>
  );
}
