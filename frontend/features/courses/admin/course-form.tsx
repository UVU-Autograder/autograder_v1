"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import type { ConceptMetadata } from "@/features/assignments/types";

export interface CourseFormUser {
  id: number;
  email: string;
  display_name: string | null;
  is_active: boolean;
}

export interface DefaultConceptsPickerProps {
  metadata: Record<string, ConceptMetadata>;
  selected: string[];
  onToggle: (key: string) => void;
}

export function DefaultConceptsPicker({
  metadata,
  selected,
  onToggle,
}: DefaultConceptsPickerProps) {
  const items = Object.values(metadata);
  if (items.length === 0) {
    return (
      <p className="text-xs text-muted-foreground italic">
        Loading concept catalog…
      </p>
    );
  }

  return (
    <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border border-border bg-muted/20 p-2">
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {items.map((item) => {
          const checked = selected.includes(item.key);
          return (
            <label
              key={item.key}
              className={`flex cursor-pointer items-start gap-2 rounded-md border p-2.5 text-left transition-colors ${
                checked
                  ? "border-success/40 bg-success/10"
                  : "border-border bg-card hover:bg-muted/50"
              }`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(item.key)}
                className="mt-0.5 size-3.5 rounded border-input text-primary focus:ring-ring"
              />
              <span className="min-w-0 space-y-1">
                <span className="block text-xs font-semibold text-foreground uppercase">
                  {item.title}
                </span>
                {(item.syntax_patterns || []).length > 0 && (
                  <span className="flex flex-wrap gap-1">
                    {item.syntax_patterns.slice(0, 3).map((pattern) => (
                      <code
                        key={pattern}
                        className="rounded border border-border bg-background px-1 py-0.5 font-mono text-[10px] text-muted-foreground"
                      >
                        {pattern}
                      </code>
                    ))}
                  </span>
                )}
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

export interface CourseFormProps {
  code: string;
  setCode: (val: string) => void;
  title: string;
  setTitle: (val: string) => void;
  term: string;
  setTerm: (val: string) => void;
  concepts: string[];
  toggleConcept: (id: string) => void;
  conceptMetadata: Record<string, ConceptMetadata>;
  users: CourseFormUser[];
  instructorId: string;
  setInstructorId: (val: string) => void;
  instructorEmail: string;
  setInstructorEmail: (val: string) => void;
  instructorName: string;
  setInstructorName: (val: string) => void;
  iaId: string;
  setIaId: (val: string) => void;
  iaEmail: string;
  setIaEmail: (val: string) => void;
  iaName: string;
  setIaName: (val: string) => void;
  showActiveToggle?: boolean;
  isActive?: boolean;
  setIsActive?: (val: boolean) => void;
  formError: string | null;
  isSubmitting: boolean;
  submitLabel: string;
  submittingLabel: string;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  codePlaceholder?: string;
  titlePlaceholder?: string;
  termPlaceholder?: string;
}

export function CourseForm({
  code,
  setCode,
  title,
  setTitle,
  term,
  setTerm,
  concepts,
  toggleConcept,
  conceptMetadata,
  users,
  instructorId,
  setInstructorId,
  instructorEmail,
  setInstructorEmail,
  instructorName,
  setInstructorName,
  iaId,
  setIaId,
  iaEmail,
  setIaEmail,
  iaName,
  setIaName,
  showActiveToggle = false,
  isActive = true,
  setIsActive,
  formError,
  isSubmitting,
  submitLabel,
  submittingLabel,
  onSubmit,
  onCancel,
  codePlaceholder,
  titlePlaceholder,
  termPlaceholder,
}: CourseFormProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4 py-2">
      <div className="space-y-1">
        <label className="text-xs font-semibold text-muted-foreground uppercase">
          Course Code
        </label>
        <Input
          placeholder={codePlaceholder}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          required
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-semibold text-muted-foreground uppercase">
          Course Title
        </label>
        <Input
          placeholder={titlePlaceholder}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-semibold text-muted-foreground uppercase">
          Term
        </label>
        <Input
          placeholder={termPlaceholder}
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-baseline justify-between gap-2">
          <label className="text-xs font-semibold text-muted-foreground uppercase">
            Default Concepts
          </label>
          <span className="text-[10px] text-muted-foreground">
            {concepts.length} selected
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          Select default allowed structures for assignments in this course.
        </p>
        <DefaultConceptsPicker
          metadata={conceptMetadata}
          selected={concepts}
          onToggle={toggleConcept}
        />
      </div>

      <div className="space-y-1">
        <label className="text-xs font-semibold text-muted-foreground uppercase">
          Instructor
        </label>
        <select
          className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          value={instructorId}
          onChange={(e) => setInstructorId(e.target.value)}
        >
          <option value="none">None</option>
          <option value="custom">+ Add by email...</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.email} {u.display_name ? `(${u.display_name})` : ""}
            </option>
          ))}
        </select>
      </div>

      {instructorId === "custom" && (
        <div className="border border-border bg-muted/30 rounded-md p-3 space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase">
              New Instructor UVU Email
            </label>
            <Input
              type="email"
              placeholder="e.g. green.scholar@uvu.edu"
              value={instructorEmail}
              onChange={(e) => setInstructorEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase">
              New Instructor Display Name (Optional)
            </label>
            <Input
              placeholder="e.g. Professor Green"
              value={instructorName}
              onChange={(e) => setInstructorName(e.target.value)}
            />
          </div>
        </div>
      )}

      <div className="space-y-1">
        <label className="text-xs font-semibold text-muted-foreground uppercase">
          IA (Teaching Assistant)
        </label>
        <select
          className="w-full rounded-md border border-input bg-background text-foreground px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          value={iaId}
          onChange={(e) => setIaId(e.target.value)}
        >
          <option value="none">None</option>
          <option value="custom">+ Add by email...</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.email} {u.display_name ? `(${u.display_name})` : ""}
            </option>
          ))}
        </select>
      </div>

      {iaId === "custom" && (
        <div className="border border-border bg-muted/30 rounded-md p-3 space-y-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase">
              New IA UVU Email
            </label>
            <Input
              type="email"
              placeholder="e.g. assistant.ta@uvu.edu"
              value={iaEmail}
              onChange={(e) => setIaEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground uppercase">
              New IA Display Name (Optional)
            </label>
            <Input
              placeholder="e.g. John TA"
              value={iaName}
              onChange={(e) => setIaName(e.target.value)}
            />
          </div>
        </div>
      )}

      {showActiveToggle && setIsActive && (
        <div className="flex items-center gap-2 pt-1">
          <input
            type="checkbox"
            id="edit-is-active"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="rounded border-input text-primary focus:ring-primary"
          />
          <label
            htmlFor="edit-is-active"
            className="text-sm font-medium text-foreground cursor-pointer"
          >
            Course is active
          </label>
        </div>
      )}

      {formError && (
        <p className="text-xs text-destructive font-medium">{formError}</p>
      )}

      <DialogFooter className="pt-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? submittingLabel : submitLabel}
        </Button>
      </DialogFooter>
    </form>
  );
}
