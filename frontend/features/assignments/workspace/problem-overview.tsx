"use client";

import React from "react";
import { Assignment, ConceptMetadata } from "@/features/assignments/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CheckCircle2Icon,
  AlertCircleIcon,
  ShieldCheckIcon,
} from "lucide-react";

type ProblemOverviewProps = {
  assignment: Assignment;
  conceptMeta?: Record<string, ConceptMetadata>;
};

export function ProblemOverview({
  assignment,
  conceptMeta = {},
}: ProblemOverviewProps) {
  const allowedConcepts = assignment.allowed_concepts || [];
  const constraints = assignment.constraints || [];

  return (
    <div className="h-full w-full overflow-y-auto p-6 bg-background space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-card rounded-xl border border-border shadow-xs">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary border border-primary/20">
              Sandbox Assignment
            </span>
          </div>
          <h1 className="text-xl font-bold text-foreground">
            {assignment.title}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-muted-foreground block uppercase font-medium">
              Max Score
            </span>
            <span className="text-lg font-bold font-mono text-success">
              {assignment.max_score} pts
            </span>
          </div>
        </div>
      </div>

      {/* Constraints & Submission Rules */}
      {constraints.length > 0 && (
        <Card className="border-warning/30 bg-warning/10 text-card-foreground">
          <CardHeader className="py-3 px-4 flex flex-row items-center gap-2">
            <AlertCircleIcon className="w-4 h-4 text-warning" />
            <CardTitle className="text-sm font-semibold text-warning">
              Submission Rules & Constraints
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2 px-4 space-y-1.5 text-xs text-muted-foreground">
            {constraints.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-warning" />
                <span>
                  <strong className="font-semibold text-foreground">{c.label}:</strong>{" "}
                  {c.value}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Allowed Concepts Whitelist */}
      <Card>
        <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className="w-4 h-4 text-primary" />
            <CardTitle className="text-sm font-semibold text-foreground">
              Allowed Concepts
            </CardTitle>
          </div>
          <span className="text-xs text-muted-foreground">
            {allowedConcepts.length > 0
              ? `${allowedConcepts.length} allowed`
              : "All concepts allowed"}
          </span>
        </CardHeader>
        <CardContent className="py-3 px-4">
          {allowedConcepts.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {allowedConcepts.map((conceptKey) => {
                const meta = conceptMeta[conceptKey];
                const title = meta?.title || conceptKey.replace(/_/g, " ");
                return (
                  <span
                    key={conceptKey}
                    className="inline-flex items-center bg-primary/10 text-primary border border-primary/20 font-medium text-xs px-2.5 py-1 rounded-md"
                    title={meta?.syntax_patterns?.join(", ") || undefined}
                  >
                    <CheckCircle2Icon className="w-3 h-3 mr-1 text-primary inline" />
                    {title}
                  </span>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground italic">
              No specific AST concept restrictions configured for this
              assignment.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ProblemOverview;
