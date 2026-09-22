"use client";

import React from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2Icon, BanIcon } from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";

export function ConceptWhitelistSection() {
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
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Inherited Module & Course Concepts</CardTitle>
            <CardDescription>
              Concepts inherited from course settings and assigned module. Click an inherited concept card to <strong>blacklist</strong> it specifically for this assignment.
            </CardDescription>
          </div>
          <Link
            href={`/staff/courses/${courseId}/settings`}
            className="text-xs text-primary font-semibold hover:underline flex items-center gap-1"
          >
            Manage Course Modules &rarr;
          </Link>
        </CardHeader>
        <CardContent>
          {inheritedConceptKeys.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {inheritedConceptKeys.map((key) => {
                const isBlacklisted = conceptDenylist.includes(key);
                const isCourse = courseDefaultConcepts.includes(key);
                const isModule = moduleConcepts.includes(key);
                const meta = conceptMeta[key];
                const displayTitle = meta?.title || key;
                const syntaxPatterns = meta?.syntax_patterns || [];
                const sourceLabel = isCourse ? "Course Default" : isModule ? "Module Default" : "Inherited";

                return (
                  <button
                    type="button"
                    key={key}
                    onClick={() => toggleConceptDenylist(key)}
                    className={`flex items-start gap-3 p-3.5 rounded-lg border text-left cursor-pointer transition-all ${
                      isBlacklisted
                        ? "bg-destructive/10 border-destructive/30 text-destructive hover:bg-destructive/15"
                        : "bg-success/10 border-success/30 text-success hover:bg-success/15"
                    }`}
                  >
                    {isBlacklisted ? (
                      <BanIcon className="w-5 h-5 text-destructive shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle2Icon className="w-5 h-5 text-success shrink-0 mt-0.5" />
                    )}

                    <div className="space-y-1.5 grow">
                      <div
                        className={`text-sm font-bold tracking-tight ${
                          isBlacklisted ? "line-through text-destructive" : "text-foreground"
                        }`}
                      >
                        {displayTitle}
                      </div>

                      {/* Display covered syntax patterns instead of raw key */}
                      {syntaxPatterns.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-0.5">
                          {syntaxPatterns.slice(0, 3).map((pat, idx) => (
                            <code
                              key={idx}
                              className={`text-xs font-mono px-1.5 py-0.5 rounded border ${
                                isBlacklisted
                                  ? "bg-destructive/15 border-destructive/30 text-destructive font-medium"
                                  : "bg-background/80 border-border text-foreground font-medium"
                              }`}
                            >
                              {pat}
                            </code>
                          ))}
                        </div>
                      )}

                      <div className="pt-1 flex items-center gap-1.5">
                        <Badge
                          variant={isBlacklisted ? "destructive" : "success"}
                          className="text-xs"
                        >
                          {isBlacklisted ? "Disabled for assignment" : sourceLabel}
                        </Badge>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="rounded-lg border border-border bg-muted/40 p-6 text-center space-y-2">
              <div className="text-sm font-semibold text-foreground">
                {moduleId === null ? "No Course Module Assigned" : "No Concepts Configured for Assigned Module"}
              </div>
              <p className="text-xs text-muted-foreground max-w-md mx-auto">
                Assign a Course Module in the General & Files tab to automatically inherit syntax boundaries across assignments.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
