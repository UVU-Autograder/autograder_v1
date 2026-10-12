"use client";

import React, { useState } from "react";
import {
  SparklesIcon,
  PlusCircleIcon,
  ReplaceIcon,
  CheckCircle2Icon,
  ShieldAlertIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api-client";

export type AITestMode = "generate" | "edge_cases" | "refine";

export interface SuggestedScoringItem {
  key: string;
  label: string;
  points: number;
}

export interface AITestAuthoringResponse {
  generated_code: string;
  suggested_items: SuggestedScoringItem[];
  explanation: string;
  used_fallback: boolean;
}

interface AITestAssistantDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  courseId: string;
  assignmentId: string;
  currentTestCode: string;
  onInsertTests: (code: string, insertMode: "append" | "replace") => void;
}

export function AITestAssistantDialog({
  isOpen,
  onOpenChange,
  courseId,
  assignmentId,
  currentTestCode,
  onInsertTests,
}: AITestAssistantDialogProps) {
  const [mode, setMode] = useState<AITestMode>("generate");
  const [instruction, setInstruction] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AITestAuthoringResponse | null>(null);
  const [editablePreview, setEditablePreview] = useState("");

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const response = await apiClient.post<AITestAuthoringResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/ai-generate-tests`,
        {
          mode,
          instruction: instruction.trim() || null,
          current_test_code: currentTestCode,
        },
      );
      setResult(response);
      setEditablePreview(response.generated_code);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate pytest test cases.",
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] w-[min(95vw,56rem)] max-w-none flex-col gap-4 overflow-y-auto p-6 sm:max-w-none">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg font-bold text-foreground">
            <SparklesIcon className="w-5 h-5 text-primary" />
            <span>AI Test Suite Assistant</span>
          </DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            Generate, discover edge cases, or refine{" "}
            <code className="font-mono bg-muted px-1 py-0.5 rounded text-foreground">
              @pytest.mark.ag_*
            </code>{" "}
            test functions using the assignment specification and reference solution.
          </DialogDescription>
        </DialogHeader>

        {/* Mode Selection */}
        <div className="space-y-2">
          <Label className="text-xs uppercase text-muted-foreground font-semibold">
            Authoring Mode
          </Label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setMode("generate")}
              className={`rounded-lg border p-3 text-left text-xs transition-colors cursor-pointer ${
                mode === "generate"
                  ? "border-primary bg-primary/10 text-foreground font-semibold"
                  : "border-border bg-card text-muted-foreground hover:text-foreground"
              }`}
              data-testid="ai-mode-generate"
            >
              <div className="font-bold text-foreground">1. Generate from Spec</div>
              <div className="mt-0.5 text-muted-foreground font-normal">
                Scaffold pytest tests from description &amp; rubric keys.
              </div>
            </button>
            <button
              type="button"
              onClick={() => setMode("edge_cases")}
              className={`rounded-lg border p-3 text-left text-xs transition-colors cursor-pointer ${
                mode === "edge_cases"
                  ? "border-primary bg-primary/10 text-foreground font-semibold"
                  : "border-border bg-card text-muted-foreground hover:text-foreground"
              }`}
              data-testid="ai-mode-edge-cases"
            >
              <div className="font-bold text-foreground">2. Discover Edge Cases</div>
              <div className="mt-0.5 text-muted-foreground font-normal">
                Suggest boundary values, empty inputs, and invariants.
              </div>
            </button>
            <button
              type="button"
              onClick={() => setMode("refine")}
              className={`rounded-lg border p-3 text-left text-xs transition-colors cursor-pointer ${
                mode === "refine"
                  ? "border-primary bg-primary/10 text-foreground font-semibold"
                  : "border-border bg-card text-muted-foreground hover:text-foreground"
              }`}
              data-testid="ai-mode-refine"
            >
              <div className="font-bold text-foreground">3. Refine Assertions</div>
              <div className="mt-0.5 text-muted-foreground font-normal">
                Prompt for custom checks or clearer failure messages.
              </div>
            </button>
          </div>
        </div>

        {/* Instructor Prompt / Specification */}
        <div className="space-y-1.5">
          <Label htmlFor="ai-test-instruction" className="text-xs font-semibold">
            Specification / Refinement Prompt (Optional)
          </Label>
          <Textarea
            id="ai-test-instruction"
            rows={3}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="e.g., Add negative number boundary checks for calculate_total(items), or make assertion failure messages more descriptive..."
            className="font-mono text-xs"
            data-testid="ai-test-instruction-input"
          />
          <div className="flex justify-end pt-1">
            <Button
              type="button"
              size="sm"
              onClick={handleGenerate}
              disabled={isGenerating}
              data-testid="ai-generate-submit-btn"
            >
              <SparklesIcon className="w-4 h-4 mr-1.5" />
              {isGenerating ? "Generating Tests..." : "Generate Pytest Preview"}
            </Button>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
            <ShieldAlertIcon className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Preview & Insertion Section */}
        {result && (
          <div className="space-y-3 border-t border-border pt-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-success">
                <CheckCircle2Icon className="w-4 h-4" />
                <span>{result.explanation}</span>
              </div>
              {result.suggested_items.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5">
                  {result.suggested_items.map((s) => (
                    <Badge key={s.key} variant="outline" className="font-mono text-xs">
                      @pytest.mark.ag_{s.key} ({s.points} pts)
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="ai-generated-code-preview" className="text-xs text-muted-foreground">
                Inspect &amp; Edit Generated Test Code Before Inserting
              </Label>
              <Textarea
                id="ai-generated-code-preview"
                rows={12}
                value={editablePreview}
                onChange={(e) => setEditablePreview(e.target.value)}
                className="font-mono text-xs"
                data-testid="ai-generated-code-preview"
              />
            </div>

            <div className="rounded-lg border border-warning/30 bg-warning/10 p-2.5 text-xs text-foreground">
              <strong>Preflight Guard:</strong> Inserting tests automatically syncs{" "}
              <code className="font-mono">@pytest.mark.ag_*</code> keys into your rubric. Run{" "}
              <strong>Model Solution Validation</strong> in Step 4 before publishing to verify all generated assertions pass your reference solution.
            </div>

            <div className="flex flex-wrap justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  onInsertTests(editablePreview, "replace");
                  onOpenChange(false);
                }}
                data-testid="ai-replace-tests-btn"
              >
                <ReplaceIcon className="w-4 h-4 mr-1.5" />
                Replace tests.py &amp; Sync Markers
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => {
                  onInsertTests(editablePreview, "append");
                  onOpenChange(false);
                }}
                data-testid="ai-append-tests-btn"
              >
                <PlusCircleIcon className="w-4 h-4 mr-1.5" />
                Append to tests.py &amp; Sync Markers
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
