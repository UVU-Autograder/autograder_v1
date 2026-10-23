"use client";

import React from "react";
import { Assignment, ConceptMetadata } from "@/features/assignments/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import MarkdownRenderer from "@/components/markdown-renderer";
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
    <div className="h-full w-full space-y-4 overflow-y-auto bg-background p-6">
      <div className="flex flex-col justify-between gap-3 rounded-xl border border-border bg-card p-4 md:flex-row md:items-center">
        <h1 className="text-xl font-bold text-foreground">{assignment.title}</h1>
        <div className="text-right">
          <span className="block text-xs font-medium uppercase text-muted-foreground">
            Max Score
          </span>
          <span className="font-mono text-lg font-bold text-success">
            {assignment.max_score} pts
          </span>
        </div>
      </div>

      {assignment.description ? (
        <Card
          size="sm"
          className="gap-1.5 py-3"
          data-testid="assignment-description-card"
        >
          <CardContent className="px-4 py-0">
            <MarkdownRenderer
              content={assignment.description}
              className="text-xs leading-relaxed text-foreground"
            />
          </CardContent>
        </Card>
      ) : null}

      {constraints.length > 0 && (
        <Card
          size="sm"
          className="gap-1.5 border-warning/30 bg-warning/10 py-3 text-card-foreground"
        >
          <CardHeader className="flex flex-row items-center gap-2 px-4 py-0">
            <AlertCircleIcon className="h-4 w-4 text-warning" />
            <CardTitle className="text-sm font-semibold text-warning">
              Submission Rules
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5 px-4 py-0 text-xs text-muted-foreground">
            {constraints.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-warning" />
                <span>
                  <strong className="font-semibold text-foreground">
                    {c.label}:
                  </strong>{" "}
                  {c.value}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="flex flex-row items-center justify-between px-4 py-0">
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className="h-4 w-4 text-primary" />
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
        {allowedConcepts.length > 0 && (
          <CardContent className="px-4 py-0">
            <div className="flex flex-wrap gap-2">
              {allowedConcepts.map((conceptKey) => {
                const meta = conceptMeta[conceptKey];
                const title = meta?.title || conceptKey.replace(/_/g, " ");
                return (
                  <span
                    key={conceptKey}
                    className="inline-flex items-center rounded-md border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary"
                    title={meta?.syntax_patterns?.join(", ") || undefined}
                  >
                    <CheckCircle2Icon className="mr-1 inline h-3 w-3 text-primary" />
                    {title}
                  </span>
                );
              })}
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
}

export default ProblemOverview;
