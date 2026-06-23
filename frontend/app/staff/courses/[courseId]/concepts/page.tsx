"use client";

import { use, useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeftIcon, SaveIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";

type CourseConceptsResponse = {
  course_id: string;
  default_concepts: string[];
};

type PageProps = {
  params: Promise<{ courseId: string }>;
};

export default function CourseConceptsPage({ params }: PageProps) {
  const { courseId } = use(params);
  const [concepts, setConcepts] = useState<string[]>([]);
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

    apiClient.get<CourseConceptsResponse>(
      `/staff/courses/${courseId}/concepts`
    ).then((data) => {
      if (active) {
        setConcepts(data.default_concepts);
        setIsLoading(false);
      }
    }).catch((err) => {
      if (active) {
        setError(err instanceof Error ? err.message : "Failed to load course concepts.");
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
        { default_concepts: concepts }
      );
      setSuccess("Course default concepts saved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save course concepts.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCheckboxChange = (concept: string) => {
    setConcepts((prev) =>
      prev.includes(concept) ? prev.filter((c) => c !== concept) : [...prev, concept]
    );
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading course concepts...</p>
      </div>
    );
  }

  const allPossibleConcepts = [
    "variables",
    "conditionals",
    "loops",
    "functions",
    "file-io",
    "image-processing",
  ];

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 space-y-1">
          <Button variant="ghost" size="sm" className="-ml-3" asChild>
            <Link href={`/staff/courses/${courseId}`}>
              <ArrowLeftIcon className="mr-1 size-4" /> Back to course details
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Course Default Concepts Whitelist</h1>
          <p className="text-slate-500">Configure default whitelisting rules that apply to all assignments in {courseId}.</p>
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

        <Card>
          <CardHeader>
            <CardTitle>Whitelisted Concepts</CardTitle>
            <CardDescription>Select default allowed structures. Any other structures will flagwarnings during execution.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {allPossibleConcepts.map((concept) => (
                <div key={concept} className="flex items-center space-x-2 border rounded-md p-3 bg-white hover:bg-slate-50 cursor-pointer">
                  <input
                    type="checkbox"
                    id={`concept-${concept}`}
                    checked={concepts.includes(concept)}
                    onChange={() => handleCheckboxChange(concept)}
                    className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label
                    htmlFor={`concept-${concept}`}
                    className="text-sm font-semibold text-slate-700 uppercase cursor-pointer flex-1"
                  >
                    {concept}
                  </label>
                </div>
              ))}
            </div>
          </CardContent>
          <CardFooter className="flex justify-end">
            <Button onClick={handleSave} disabled={isSaving}>
              <SaveIcon className="mr-2 size-4" /> Save Default Whitelist
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
