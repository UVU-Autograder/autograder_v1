"use client";

import { use, useState, useEffect } from "react";
import { SaveIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
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

export default function CourseConceptsPage({ params }: PageProps) {
  const { courseId } = use(params);
  const [concepts, setConcepts] = useState<string[]>([]);
  const [modules, setModules] = useState<ModuleConfig[]>([]);
  const [metadata, setMetadata] = useState<Record<string, ConceptMetadata>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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
      setSuccess(
        "Course concepts and modules configuration saved successfully.",
      );
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save course concepts.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddModule = () => {
    setModules((prev) => [
      ...prev,
      { id: null, name: `Module ${prev.length + 1}`, concepts: [] },
    ]);
  };

  const handleRemoveModule = (index: number) => {
    setModules((prev) => prev.filter((_, i) => i !== index));
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
          const concepts = m.concepts.includes(conceptKey)
            ? m.concepts.filter((c) => c !== conceptKey)
            : [...m.concepts, conceptKey];
          return { ...m, concepts };
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
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">
          Loading course concepts...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 space-y-1">
          <BackLink
            href={`/staff/courses/${courseId}/assignments`}
            variant="compact"
          >
            Back to course details
          </BackLink>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Course Default Concepts
          </h1>
          <p className="text-slate-500">
            Configure default whitelisting rules that apply to all assignments
            in {courseId}.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-600">
            {success}
          </div>
        )}

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Base Concepts</CardTitle>
            <CardDescription>
              Select default allowed structures. Any other structures will flag
              warnings during execution.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {Object.values(metadata).map((item) => (
                <div
                  key={item.key}
                  className="flex items-start space-x-3 border rounded-md p-3 bg-white hover:bg-slate-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    id={`concept-${item.key}`}
                    checked={concepts.includes(item.key)}
                    onChange={() => handleCheckboxChange(item.key)}
                    className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 mt-1"
                  />
                  <div className="space-y-0.5 flex-1">
                    <label
                      htmlFor={`concept-${item.key}`}
                      className="text-sm font-semibold text-slate-700 uppercase cursor-pointer block"
                    >
                      {item.title}
                    </label>
                    <ul className="text-xs text-slate-400 leading-relaxed list-disc pl-4 mt-1 space-y-0.5">
                      {(item.syntax_patterns || []).map((p) => (
                        <li key={p}>{p}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end">
            <Button onClick={handleSave} disabled={isSaving}>
              <SaveIcon className="mr-2 size-4" /> Save Whitelist & Modules
            </Button>
          </CardFooter>
        </Card>

        <div className="mt-8 mb-6 space-y-1">
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Course Modules & Concept Coverages
          </h2>
          <p className="text-slate-500">
            Define course modules. Map specific allowed concepts to each module.
            Assignments will inherit these whitelisted concepts.
          </p>
        </div>

        {modules.map((mod, modIdx) => (
          <Card key={modIdx} className="mb-4">
            <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
              <div className="flex-1 mr-4">
                <Input
                  value={mod.name}
                  onChange={(e) => handleModuleRename(modIdx, e.target.value)}
                  placeholder="e.g. Module 1: Basics"
                  className="font-semibold text-slate-800 text-sm"
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="text-red-500 hover:text-red-700 hover:bg-red-50 cursor-pointer"
                onClick={() => handleRemoveModule(modIdx)}
              >
                Delete Module
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs font-medium text-slate-500">
                Concepts covered in this module:
              </p>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {Object.values(metadata).map((item) => (
                  <label
                    key={item.key}
                    className="flex items-center space-x-2 border rounded-md p-2 bg-white hover:bg-slate-50 cursor-pointer text-xs"
                  >
                    <input
                      type="checkbox"
                      checked={mod.concepts.includes(item.key)}
                      onChange={() =>
                        handleModuleConceptToggle(modIdx, item.key)
                      }
                      className="size-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="font-semibold text-slate-700 uppercase">
                      {item.title}
                    </span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}

        <div className="mt-4 mb-8">
          <Button
            type="button"
            variant="outline"
            className="w-full border-dashed py-6 hover:bg-indigo-50/50 hover:text-indigo-600 cursor-pointer"
            onClick={handleAddModule}
          >
            + Add Course Module
          </Button>
        </div>
      </div>
    </div>
  );
}
