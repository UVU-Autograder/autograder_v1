"use client";

import React from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2Icon, BanIcon } from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";

export function ConceptDenylistSection() {
  const {
    courseId,
    moduleId,
    conceptDenylist,
    toggleConceptDenylist,
    courseDefaultConcepts,
    inheritedConcepts,
    moduleConcepts,
    conceptMeta,
  } = useAssignmentEditor();

  const inheritedConceptKeys = inheritedConcepts || [];

  return (
    <Card size="sm" className="gap-1.5 py-3">
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2 px-4 py-0">
        <CardTitle className="text-base">Concepts</CardTitle>
        <Link
          href={`/staff/courses/${courseId}/settings`}
          className="text-xs font-semibold text-primary hover:underline"
        >
          Course settings
        </Link>
      </CardHeader>
      <CardContent className="px-4 py-0">
        {inheritedConceptKeys.length > 0 ? (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 md:grid-cols-3">
            {inheritedConceptKeys.map((key) => {
              const isBlacklisted = conceptDenylist.includes(key);
              const isCourse = courseDefaultConcepts.includes(key);
              const isModule = moduleConcepts.includes(key);
              const meta = conceptMeta[key];
              const displayTitle = meta?.title || key;
              const syntaxPatterns = meta?.syntax_patterns || [];
              const sourceLabel = isCourse
                ? "Course"
                : isModule
                  ? "Module"
                  : "Inherited";

              return (
                <button
                  type="button"
                  key={key}
                  onClick={() => toggleConceptDenylist(key)}
                  title="Click to enable or disable for this assignment"
                  className={`flex cursor-pointer items-start gap-2 rounded-lg border p-2.5 text-left transition-colors ${
                    isBlacklisted
                      ? "border-destructive/30 bg-destructive/10 text-destructive hover:bg-destructive/15"
                      : "border-success/30 bg-success/10 text-success hover:bg-success/15"
                  }`}
                >
                  {isBlacklisted ? (
                    <BanIcon className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                  ) : (
                    <CheckCircle2Icon className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  )}

                  <div className="min-w-0 grow space-y-1">
                    <div
                      className={`text-sm font-semibold tracking-tight ${
                        isBlacklisted
                          ? "text-destructive line-through"
                          : "text-foreground"
                      }`}
                    >
                      {displayTitle}
                    </div>

                    {syntaxPatterns.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {syntaxPatterns.slice(0, 3).map((pat, idx) => (
                          <code
                            key={idx}
                            className={`rounded border px-1.5 py-0.5 font-mono text-xs ${
                              isBlacklisted
                                ? "border-destructive/30 bg-destructive/15 text-destructive"
                                : "border-border bg-background/80 text-foreground"
                            }`}
                          >
                            {pat}
                          </code>
                        ))}
                      </div>
                    )}

                    <Badge
                      variant={isBlacklisted ? "destructive" : "success"}
                      className="text-xs"
                    >
                      {isBlacklisted ? "Disabled" : sourceLabel}
                    </Badge>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">
            {moduleId === null
              ? "Assign a module under General & Files to inherit concepts."
              : "No concepts configured for this module."}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
