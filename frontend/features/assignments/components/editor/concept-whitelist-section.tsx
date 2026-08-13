"use client";

import React from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
            className="text-xs text-indigo-600 font-semibold hover:underline flex items-center gap-1"
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
                        ? "bg-rose-50 dark:bg-rose-950/50 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200 hover:bg-rose-100/70"
                        : "bg-emerald-50/60 dark:bg-emerald-950/50 border-emerald-300 dark:border-emerald-800 text-emerald-950 dark:text-emerald-200 hover:bg-emerald-100/70"
                    }`}
                  >
                    {isBlacklisted ? (
                      <BanIcon className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle2Icon className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                    )}

                    <div className="space-y-1.5 grow">
                      <div
                        className={`text-sm font-bold tracking-tight ${
                          isBlacklisted ? "line-through text-rose-700 dark:text-rose-400" : "text-foreground"
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
                              className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                                isBlacklisted
                                  ? "bg-rose-100/80 dark:bg-rose-900/60 border-rose-200 dark:border-rose-700 text-rose-800 dark:text-rose-200"
                                  : "bg-white/80 dark:bg-slate-900 border-emerald-200 dark:border-emerald-700 text-emerald-900 dark:text-emerald-200"
                              }`}
                            >
                              {pat}
                            </code>
                          ))}
                        </div>
                      )}

                      <div className="pt-1 flex items-center gap-1.5">
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                            isBlacklisted
                              ? "bg-rose-200 dark:bg-rose-900/80 text-rose-900 dark:text-rose-100"
                              : "bg-emerald-200 dark:bg-emerald-900/80 text-emerald-900 dark:text-emerald-100"
                          }`}
                        >
                          {isBlacklisted ? "Disabled for assignment" : sourceLabel}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-6 text-center space-y-2">
              <div className="text-sm font-semibold text-slate-700">
                {moduleId === null ? "No Course Module Assigned" : "No Concepts Configured for Assigned Module"}
              </div>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Assign a Course Module in the General & Files tab to automatically inherit syntax boundaries across assignments.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
