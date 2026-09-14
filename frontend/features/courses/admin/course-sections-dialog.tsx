"use client";

import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { CourseAdminDetail } from "@/features/courses/types";
import {
  SectionAdminDetail,
  getCourseSections,
  createAdminSection,
  updateAdminSection,
  deleteAdminSection,
} from "@/features/courses/api";

interface CourseSectionsDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  course: CourseAdminDetail | null;
}

export function CourseSectionsDialog({
  isOpen,
  onOpenChange,
  course,
}: CourseSectionsDialogProps) {
  const [sections, setSections] = useState<SectionAdminDetail[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [newCrn, setNewCrn] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSections = useCallback(async () => {
    if (!course) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await getCourseSections(course.id);
      setSections(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load sections.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [course]);

  useEffect(() => {
    if (isOpen && course) {
      setNewCrn("");
      setError(null);
      void fetchSections();
    }
  }, [isOpen, course, fetchSections]);

  const handleAddSection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!course || !newCrn.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await createAdminSection(course.id, { crn: newCrn.trim() });
      setNewCrn("");
      await fetchSections();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create section.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleActive = async (section: SectionAdminDetail) => {
    setError(null);
    try {
      if (section.is_active) {
        await deleteAdminSection(section.id);
      } else {
        await updateAdminSection(section.id, { is_active: true });
      }
      await fetchSections();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update section status.",
      );
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-lg overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Manage Sections — {course?.code.toUpperCase()}</DialogTitle>
          <DialogDescription>
            Add or deactivate course CRNs for {course?.title}.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleAddSection} className="flex gap-2 pt-2">
          <Input
            placeholder="e.g. 21456"
            value={newCrn}
            onChange={(e) => setNewCrn(e.target.value)}
            className="text-sm font-mono"
            required
            aria-label="Section CRN"
          />
          <Button type="submit" disabled={isSubmitting || !newCrn.trim()} size="sm">
            {isSubmitting ? "Adding..." : "Add Section"}
          </Button>
        </form>

        {error && (
          <p className="text-xs text-destructive font-medium">{error}</p>
        )}

        <div className="space-y-2 pt-2">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase">
            Active & Inactive Sections ({sections.length})
          </h4>

          {isLoading ? (
            <p className="animate-pulse text-xs text-muted-foreground py-4 text-center">
              Loading sections...
            </p>
          ) : sections.length === 0 ? (
            <p className="text-xs text-muted-foreground italic py-4 text-center">
              No sections created yet for this course.
            </p>
          ) : (
            <div className="space-y-1.5 max-h-60 overflow-y-auto">
              {sections.map((section) => (
                <div
                  key={section.id}
                  className="flex items-center justify-between rounded-md border border-border p-2.5 bg-card text-card-foreground text-sm"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-medium">CRN: {section.crn}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${
                        section.is_active
                          ? "bg-success/15 text-success border border-success/30"
                          : "bg-muted text-muted-foreground border border-border"
                      }`}
                    >
                      {section.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Button
                      type="button"
                      variant={section.is_active ? "outline" : "default"}
                      size="sm"
                      className="h-7 text-xs px-2.5"
                      onClick={() => handleToggleActive(section)}
                    >
                      {section.is_active ? "Deactivate" : "Activate"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
