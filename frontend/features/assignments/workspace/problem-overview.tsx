"use client";

import React from "react";
import { Assignment, ConceptMetadata } from "@/features/assignments/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2Icon, AlertCircleIcon, ShieldCheckIcon } from "lucide-react";

type ProblemOverviewProps = {
  assignment: Assignment;
  conceptMeta?: Record<string, ConceptMetadata>;
};

export function ProblemOverview({ assignment, conceptMeta = {} }: ProblemOverviewProps) {
  const allowedConcepts = assignment.allowed_concepts || [];
  const constraints = assignment.constraints || [];

  return (
    <div className="h-full w-full overflow-y-auto p-6 bg-stone-50/50 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-white rounded-xl border border-stone-200 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
              Sandbox Assignment
            </span>
          </div>
          <h1 className="text-xl font-bold text-stone-900">{assignment.title}</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-stone-500 block uppercase font-medium">Max Score</span>
            <span className="text-lg font-bold font-mono text-emerald-600">{assignment.max_score} pts</span>
          </div>
        </div>
      </div>

      {/* Constraints & Submission Rules */}
      {constraints.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/30">
          <CardHeader className="py-3 px-4 flex flex-row items-center gap-2">
            <AlertCircleIcon className="w-4 h-4 text-amber-600" />
            <CardTitle className="text-sm font-semibold text-amber-900">
              Submission Rules & Constraints
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2 px-4 space-y-1.5 text-xs text-amber-900/90">
            {constraints.map((c, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span>
                  <strong className="font-semibold">{c.label}:</strong> {c.value}
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
            <ShieldCheckIcon className="w-4 h-4 text-indigo-600" />
            <CardTitle className="text-sm font-semibold text-stone-900">
              Allowed Concepts Whitelist
            </CardTitle>
          </div>
          <span className="text-xs text-stone-500">
            {allowedConcepts.length > 0 ? `${allowedConcepts.length} allowed` : "All concepts allowed"}
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
                    className="inline-flex items-center bg-indigo-50 text-indigo-700 border border-indigo-200/60 font-medium text-xs px-2.5 py-1 rounded-md"
                    title={meta?.syntax_patterns?.join(", ") || undefined}
                  >
                    <CheckCircle2Icon className="w-3 h-3 mr-1 text-indigo-500 inline" />
                    {title}
                  </span>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-stone-500 italic">
              No specific AST concept restrictions configured for this assignment.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ProblemOverview;
