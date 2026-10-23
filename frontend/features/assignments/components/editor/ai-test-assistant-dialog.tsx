"use client";

import React, { useState } from "react";
import {
  SparklesIcon,
  PlusCircleIcon,
  ReplaceIcon,
  CheckCircle2Icon,
  ShieldAlertIcon,
  RefreshCwIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api-client";

export interface AITestAuthoringResponse {
  generated_code: string;
  explanation: string;
}

interface AITestAssistantDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  courseId: string;
  assignmentId: string;
  assignmentDescription: string;
  currentTestCode: string;
  onInsertTests: (code: string, insertMode: "append" | "replace") => void;
}

export function AITestAssistantDialog({
  isOpen,
  onOpenChange,
  courseId,
  assignmentId,
  assignmentDescription,
  currentTestCode,
  onInsertTests,
}: AITestAssistantDialogProps) {
  const [instruction, setInstruction] = useState(assignmentDescription);
  const [prevOpen, setPrevOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AITestAuthoringResponse | null>(null);
  const [editablePreview, setEditablePreview] = useState("");

  if (isOpen && !prevOpen) {
    setPrevOpen(true);
    setInstruction(assignmentDescription);
    setResult(null);
    setEditablePreview("");
    setError(null);
  } else if (!isOpen && prevOpen) {
    setPrevOpen(false);
  }

  const hasPreview = Boolean(editablePreview.trim());
  const suiteForRequest = hasPreview ? editablePreview : currentTestCode;

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    try {
      const response = await apiClient.post<AITestAuthoringResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/ai-generate-tests`,
        {
          instruction: instruction.trim() || null,
          current_test_code: suiteForRequest || null,
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
      <DialogContent className="flex max-h-[90vh] w-[min(95vw,48rem)] max-w-none flex-col gap-4 overflow-y-auto p-6 sm:max-w-none">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg font-bold text-foreground">
            <SparklesIcon className="w-5 h-5 text-primary" />
            <span>AI Test Assistant</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-1.5">
          <Label htmlFor="ai-test-instruction" className="text-xs font-semibold">
            Instructions
          </Label>
          <Textarea
            id="ai-test-instruction"
            rows={5}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder={
              hasPreview
                ? "Describe changes to the preview…"
                : "Assignment specification or what to generate…"
            }
            className="font-mono text-xs"
            data-testid="ai-test-instruction-input"
          />
          <div className="flex flex-wrap justify-end gap-2 pt-1">
            <Button
              type="button"
              size="sm"
              onClick={handleGenerate}
              disabled={isGenerating}
              data-testid="ai-generate-submit-btn"
            >
              {hasPreview ? (
                <RefreshCwIcon className="w-4 h-4 mr-1.5" />
              ) : (
                <SparklesIcon className="w-4 h-4 mr-1.5" />
              )}
              {isGenerating ? "Working…" : hasPreview ? "Revise" : "Generate"}
            </Button>
          </div>
        </div>

        {error && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
            <ShieldAlertIcon className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="space-y-3 border-t border-border pt-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-success">
              <CheckCircle2Icon className="w-4 h-4" />
              <span>{result.explanation}</span>
            </div>

            <div className="space-y-1">
              <Label
                htmlFor="ai-generated-code-preview"
                className="text-xs text-muted-foreground"
              >
                Preview
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
                Replace tests.py
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
                Append to tests.py
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
