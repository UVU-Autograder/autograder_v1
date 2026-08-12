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
                        ? "bg-red-50 border-red-300 text-red-900 hover:bg-red-100/70"
                        : "bg-indigo-50/60 border-indigo-200 text-indigo-950 hover:bg-indigo-100/70"
                    }`}
                  >
                    {isBlacklisted ? (
                      <BanIcon className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle2Icon className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
                    )}

                    <div className="space-y-1.5 grow">
                      <div
                        className={`text-sm font-bold tracking-tight ${
                          isBlacklisted ? "line-through text-red-700" : "text-slate-900"
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
                                  ? "bg-red-100/80 border-red-200 text-red-800"
                                  : "bg-white/80 border-indigo-200 text-indigo-900"
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
                              ? "bg-red-200 text-red-900"
                              : "bg-indigo-100 text-indigo-800 border border-indigo-200"
                          }`}
                        >
                          {isBlacklisted ? "Blacklisted for Assignment" : `Allowed (${sourceLabel})`}
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
