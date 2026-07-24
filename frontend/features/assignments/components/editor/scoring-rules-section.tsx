"use client";

import React, { useState, useEffect } from "react";
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
} from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";
import { apiClient } from "@/lib/api-client";

export function ScoringRulesSection() {
  const {
    courseId,
    assignmentId,
    scoringItems,
    addScoringItem,
    removeScoringItem,
    updateScoringItemField,
    autoGenerateKeyFromLabel,
    artifacts,
    refreshArtifacts,
    syncMarkersFromTestSuite,
    handleSave,
    setErrorMessage,
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

  // Pytest test code state
  const [codeText, setCodeText] = useState("");
  const [loadingCode, setLoadingCode] = useState(true);
  const [savingCode, setSavingCode] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Dynamic lookup for server pytest artifact
  const pytestArtifact = artifacts.find(
    (a) =>
      a.artifact_type === "pytest_file" ||
      a.artifact_key === "assignment_tests",
  );
  const artifactKey = pytestArtifact?.artifact_key || "assignment_tests";

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoadingCode(true);
      try {
        const text = await apiClient.getText(
          `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${artifactKey}`,
        );
        if (!cancelled) {
          setCodeText(text);
        }
      } catch {
        if (!cancelled) {
          setCodeText(
            `import pytest\n\n@pytest.mark.ag_main\ndef test_main_function():\n    assert True\n`,
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingCode(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [courseId, assignmentId, artifactKey]);

  const handleSyncFromCode = () => {
    const addedCount = syncMarkersFromTestSuite(codeText);
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

  const handleSaveCodeAndRubric = async () => {
    setSavingCode(true);
    setSaveSuccess(false);
    try {
      // 1. Save tests.py code artifact to server
      const file = new File([codeText], "tests.py", { type: "text/plain" });
      const formData = new FormData();
      formData.append("file", file);
      formData.append("artifact_key", artifactKey);
      formData.append("artifact_type", "pytest_file");

      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData,
      );
      await refreshArtifacts();

      // 2. Save full assignment setup (rubric items + config)
      await handleSave();
      setSaveSuccess(true);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : "Failed to save test suite & rubric.",
      );
    } finally {
      setSavingCode(false);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([codeText], { type: "text/plain" });
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
              <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-700">
                tests.py
              </code>
              . Base Total:{" "}
              <strong className="text-slate-900 font-mono">
                {totalBasePoints} pts
              </strong>
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
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
          <div className="space-y-3">
            {pytestItems.map((item) => (
              <div
                key={item.key}
                className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3 bg-stone-50 rounded-lg border border-stone-200 items-center text-sm"
              >
                {/* Key / Slug */}
                <div className="md:col-span-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-stone-500 uppercase">
                      Key / Pytest Marker
                    </span>
                    <button
                      type="button"
                      onClick={() => autoGenerateKeyFromLabel(item.key)}
                      className="text-[10px] flex items-center gap-1 text-indigo-600 font-semibold hover:text-indigo-800 hover:underline cursor-pointer"
                      title="Auto-generate key from description"
                    >
                      Auto-generate key
                    </button>
                  </div>
                  <div className="relative flex items-center">
                    <span className="absolute left-2.5 text-xs font-mono font-bold text-stone-500 select-none pointer-events-none">
                      ag_
                    </span>
                    <Input
                      value={item.key}
                      onChange={(e) =>
                        updateScoringItemField(item.key, "key", e.target.value)
                      }
                      className="font-mono text-xs pl-8"
                    />
                  </div>
                </div>

                {/* Label / Description Header */}
                <div className="md:col-span-5 space-y-1">
                  <span className="text-[10px] font-bold text-stone-500 uppercase">
                    Description
                  </span>
                  <Input
                    value={item.label}
                    onChange={(e) =>
                      updateScoringItemField(item.key, "label", e.target.value)
                    }
                    placeholder="e.g. Basic Calculator Operations"
                  />
                </div>

                {/* Points */}
                <div className="md:col-span-2 space-y-1">
                  <span className="text-[10px] font-bold text-stone-500 uppercase">
                    Points
                  </span>
                  <Input
                    type="number"
                    value={item.points}
                    onChange={(e) =>
                      updateScoringItemField(
                        item.key,
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
                    onClick={() => removeScoringItem(item.key)}
                  >
                    <Trash2Icon className="w-4 h-4 text-red-500" />
                  </Button>
                </div>

                {/* Expected I/O Preview */}
                <div className="md:col-span-12 mt-1 pt-2 border-t border-stone-200 flex flex-wrap items-center gap-3 text-xs text-stone-600">
                  <span className="font-semibold text-stone-700 flex items-center gap-1">
                    <FileTextIcon className="w-3.5 h-3.5 text-indigo-600" />
                    Parsed Expected I/O:
                  </span>
                  {((item.inputs && item.inputs.length > 0) || (item.outputs && item.outputs.length > 0)) ? (
                    <div className="flex flex-wrap items-center gap-2">
                      {item.inputs && item.inputs.length > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-blue-50 text-blue-700 border border-blue-200" title="Expected Input">
                          <strong className="mr-1 font-sans font-semibold">Input:</strong> {item.inputs.join(", ")}
                        </span>
                      )}
                      {item.outputs && item.outputs.length > 0 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200" title="Expected Output">
                          <strong className="mr-1 font-sans font-semibold">Output:</strong> {item.outputs.join(", ")}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-[11px] text-stone-400 italic">
                      No EXPECTED_INPUT or EXPECTED_OUTPUT constants detected in test code for marker ag_{item.key}.
                    </span>
                  )}
                </div>
              </div>
            ))}

            {pytestItems.length === 0 && (
              <p className="text-xs text-stone-400 italic p-4 text-center border border-dashed rounded-lg">
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
                key={item.key}
                className="grid grid-cols-1 md:grid-cols-12 gap-3 p-3 bg-purple-50/50 rounded-lg border border-purple-200 items-center text-sm"
              >
                {/* Key / Slug */}
                <div className="md:col-span-4 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-stone-500 uppercase">
                      Manual Key
                    </span>
                    <button
                      type="button"
                      onClick={() => autoGenerateKeyFromLabel(item.key)}
                      className="text-[10px] flex items-center gap-1 text-purple-600 font-semibold hover:text-purple-800 hover:underline cursor-pointer"
                      title="Auto-generate key from label"
                    >
                      Auto-generate key
                    </button>
                  </div>
                  <Input
                    value={item.key}
                    onChange={(e) =>
                      updateScoringItemField(item.key, "key", e.target.value)
                    }
                    className="font-mono text-xs"
                  />
                </div>

                {/* Label / Description Header */}
                <div className="md:col-span-5 space-y-1">
                  <span className="text-[10px] font-bold text-stone-500 uppercase">
                    Criterion Label
                  </span>
                  <Input
                    value={item.label}
                    onChange={(e) =>
                      updateScoringItemField(item.key, "label", e.target.value)
                    }
                    placeholder="e.g. Code Formatting & Comments"
                  />
                </div>

                {/* Points */}
                <div className="md:col-span-2 space-y-1">
                  <span className="text-[10px] font-bold text-stone-500 uppercase">
                    Points
                  </span>
                  <Input
                    type="number"
                    value={item.points}
                    onChange={(e) =>
                      updateScoringItemField(
                        item.key,
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
                    onClick={() => removeScoringItem(item.key)}
                  >
                    <Trash2Icon className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}

            {manualItems.length === 0 && (
              <p className="text-xs text-stone-400 italic p-4 text-center border border-dashed rounded-lg">
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
              <FileTextIcon className="w-5 h-5 text-indigo-600" />
              <span>Assignment Test Suite</span>
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {saveSuccess && (
              <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1">
                <CheckCircle2Icon className="w-4 h-4" /> Saved tests.py & rubric
              </span>
            )}
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <DownloadIcon className="w-4 h-4 mr-1.5" /> Download tests.py
            </Button>
            <Button
              size="sm"
              onClick={handleSaveCodeAndRubric}
              disabled={savingCode}
            >
              <SaveIcon className="w-4 h-4 mr-1.5" />
              {savingCode ? "Saving..." : "Save Test Suite & Rubric"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-[520px] rounded-lg border border-slate-200 overflow-hidden bg-slate-900">
            {loadingCode ? (
              <div className="flex items-center justify-center h-full text-xs text-slate-400 font-mono animate-pulse">
                Fetching tests.py source code from server...
              </div>
            ) : (
              <MonacoEditor
                height="100%"
                width="100%"
                defaultLanguage="python"
                value={codeText}
                onChange={(val) => setCodeText(val || "")}
              />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
