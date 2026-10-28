"use client";

import { use, useState, useEffect } from "react";
import { SaveIcon } from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { PageLoading } from "@/components/page-status";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api-client";
import { getConceptsMetadata } from "@/features/assignments/api";
import { ConceptMetadata } from "@/features/assignments/types";

type ModuleConfig = {
  id: number | null;
  name: string;
  concepts: string[];
};

type CourseConceptsResponse = {
  course_id: string;
  default_concepts: string[];
  modules: ModuleConfig[];
};

type PageProps = {
  params: Promise<{ courseId: string }>;
};

function CompactConceptGrid({
  idPrefix,
  metadata,
  selected,
  onToggle,
}: {
  idPrefix: string;
  metadata: Record<string, ConceptMetadata>;
  selected: string[];
  onToggle: (key: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
      {Object.values(metadata).map((item) => {
        const id = `${idPrefix}-${item.key}`;
        return (
          <label
            key={item.key}
            htmlFor={id}
            className="flex cursor-pointer items-center gap-2 rounded-sm px-1 py-1.5 hover:bg-muted/40"
            title={item.syntax_patterns?.join(", ") || undefined}
          >
            <input
              type="checkbox"
              id={id}
              checked={selected.includes(item.key)}
              onChange={() => onToggle(item.key)}
              className="size-3.5 shrink-0 rounded border-input text-primary focus:ring-ring"
            />
            <span className="truncate text-sm text-foreground">{item.title}</span>
          </label>
        );
      })}
    </div>
  );
}

export default function CourseConceptsPage({ params }: PageProps) {
  const { courseId } = use(params);
  const [concepts, setConcepts] = useState<string[]>([]);
  const [modules, setModules] = useState<ModuleConfig[]>([]);
  const [metadata, setMetadata] = useState<Record<string, ConceptMetadata>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [openModuleIdx, setOpenModuleIdx] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        setIsLoading(true);
        setError(null);
      }
    });

    Promise.all([
      apiClient.get<CourseConceptsResponse>(
        `/staff/courses/${courseId}/concepts`,
      ),
      getConceptsMetadata(),
    ])
      .then(([courseData, metaData]) => {
        if (active) {
          setConcepts(courseData.default_concepts);
          setModules(courseData.modules || []);
          setMetadata(metaData);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load course concepts.",
          );
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [courseId]);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await apiClient.put<CourseConceptsResponse>(
        `/staff/courses/${courseId}/concepts`,
        {
          default_concepts: concepts,
          modules: modules,
        },
      );
      setSuccess("Course settings saved.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save course settings.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddModule = () => {
    setModules((prev) => {
      const next = [
        ...prev,
        { id: null, name: `Module ${prev.length + 1}`, concepts: [] },
      ];
      setOpenModuleIdx(next.length - 1);
      return next;
    });
  };

  const handleRemoveModule = (index: number) => {
    setModules((prev) => prev.filter((_, i) => i !== index));
    setOpenModuleIdx((prev) => {
      if (prev === null) return null;
      if (prev === index) return null;
      if (prev > index) return prev - 1;
      return prev;
    });
  };

  const handleModuleRename = (index: number, newName: string) => {
    setModules((prev) =>
      prev.map((m, i) => (i === index ? { ...m, name: newName } : m)),
    );
  };

  const handleModuleConceptToggle = (index: number, conceptKey: string) => {
    setModules((prev) =>
      prev.map((m, i) => {
        if (i === index) {
          const next = m.concepts.includes(conceptKey)
            ? m.concepts.filter((c) => c !== conceptKey)
            : [...m.concepts, conceptKey];
          return { ...m, concepts: next };
        }
        return m;
      }),
    );
  };

  const handleCheckboxChange = (concept: string) => {
    setConcepts((prev) =>
      prev.includes(concept)
        ? prev.filter((c) => c !== concept)
        : [...prev, concept],
    );
  };

  if (isLoading) {
    return <PageLoading className="h-screen">Loading course settings...</PageLoading>;
  }

  const conceptCount = Object.keys(metadata).length;

  return (
    <div className="mx-auto w-full max-w-2xl px-4 pt-8 pb-16">
      <Breadcrumbs
        items={[
          { label: "Courses", href: "/staff/courses" },
          { label: "Assignments", href: `/staff/courses/${courseId}/assignments` },
          { label: "Settings" },
        ]}
      />

      <AdminPageHeader
        title="Course settings"
        description={`Default allowed concepts and modules for ${courseId.toUpperCase()}.`}
        actions={
          <Button onClick={handleSave} disabled={isSaving}>
            <SaveIcon className="mr-1.5 size-4" />
            {isSaving ? "Saving..." : "Save"}
          </Button>
        }
      />

      {error && (
        <div className="mb-4 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-md border border-success/30 bg-success/10 p-3 text-sm text-success">
          {success}
        </div>
      )}

      <section className="mb-8 space-y-2">
        <div className="flex items-baseline justify-between gap-3">
          <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
            Default concepts
          </h2>
          <p className="text-xs text-muted-foreground">
            {concepts.length} of {conceptCount} allowed
          </p>
        </div>
        <p className="text-sm text-muted-foreground">
          Hover a name for syntax details. Unchecked concepts warn on student runs.
        </p>
        <CompactConceptGrid
          idPrefix="default"
          metadata={metadata}
          selected={concepts}
          onToggle={handleCheckboxChange}
        />
      </section>

      <section className="space-y-3">
        <div className="flex items-baseline justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
              Modules
            </h2>
            <p className="text-sm text-muted-foreground">
              Expand a module to set its concept coverage.
            </p>
          </div>
          <Button type="button" variant="outline" size="sm" onClick={handleAddModule}>
            Add module
          </Button>
        </div>

        {modules.length === 0 ? (
          <p className="py-3 text-sm text-muted-foreground">No modules yet.</p>
        ) : (
          <ul className="divide-y divide-border border-y border-border">
            {modules.map((mod, modIdx) => {
              const isOpen = openModuleIdx === modIdx;
              return (
                <li key={modIdx} className="py-2">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                    <button
                      type="button"
                      className="shrink-0 text-left text-xs font-medium text-primary hover:underline"
                      onClick={() =>
                        setOpenModuleIdx(isOpen ? null : modIdx)
                      }
                      aria-expanded={isOpen}
                    >
                      {isOpen ? "Hide concepts" : "Edit concepts"}
                    </button>
                    <Input
                      value={mod.name}
                      onChange={(e) => handleModuleRename(modIdx, e.target.value)}
                      placeholder="e.g. Module 1: Basics"
                      className="h-8 font-medium"
                      aria-label={`Module ${modIdx + 1} name`}
                    />
                    <span className="shrink-0 text-xs text-muted-foreground sm:w-24 sm:text-right">
                      {mod.concepts.length} selected
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="shrink-0 text-destructive hover:bg-destructive/10"
                      onClick={() => handleRemoveModule(modIdx)}
                    >
                      Remove
                    </Button>
                  </div>
                  {isOpen ? (
                    <div className="mt-3 pl-1">
                      <CompactConceptGrid
                        idPrefix={`module-${modIdx}`}
                        metadata={metadata}
                        selected={mod.concepts}
                        onToggle={(key) => handleModuleConceptToggle(modIdx, key)}
                      />
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
