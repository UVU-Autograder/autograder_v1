"use client";
 
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ApiError, apiClient } from "@/lib/api-client";
import { AssignmentCreatePayload } from "./types";
import { createStaffAssignment } from "./api";

const SLUG_PATTERN = /^[a-z][a-z0-9-]*$/;

type ModuleConfig = {
  id: number;
  name: string;
};

type CourseConceptsResponse = {
  course_id: string;
  default_concepts: string[];
  modules: ModuleConfig[];
};

type CreateAssignmentFormValues = {
  slug: string;
  title: string;
  language: string;
  canvas_ref: string;
  sandbox_enabled: boolean;
  module_id: string;
};

export default function CreateAssignment({ courseId }: { courseId: string }) {
  const router = useRouter();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [courseModules, setCourseModules] = useState<ModuleConfig[]>([]);

  useEffect(() => {
    apiClient.get<CourseConceptsResponse>(`/staff/courses/${courseId}/concepts`)
      .then((data) => {
        setCourseModules(data.modules || []);
      })
      .catch(() => {});
  }, [courseId]);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<CreateAssignmentFormValues>({
    defaultValues: {
      slug: "",
      title: "",
      language: "python",
      canvas_ref: "",
      sandbox_enabled: true,
      module_id: "none",
    },
  });

  const onSubmit = async (values: CreateAssignmentFormValues) => {
    setSubmitError(null);

    const payload: AssignmentCreatePayload = {
      slug: values.slug.trim(),
      title: values.title.trim(),
      language: values.language,
      sandbox_enabled: values.sandbox_enabled,
    };

    const canvasRef = values.canvas_ref.trim();
    if (canvasRef) {
      payload.canvas_ref = canvasRef;
    }

    if (values.module_id && values.module_id !== "none") {
      payload.module_id = parseInt(values.module_id, 10);
    } else {
      payload.module_id = null;
    }

    try {
      const created = await createStaffAssignment(courseId, payload);
      router.push(`/staff/courses/${courseId}/assignments/${created.assignment_id}`);
    } catch (error) {
      if (error instanceof ApiError) {
        setSubmitError(error.message);
        return;
      }
      setSubmitError("Failed to create assignment. Please try again.");
    }
  };

  return (
    <div className="w-full px-4 pt-8">
      <div className="mx-auto max-w-lg">
        <div className="mb-6">
          <BackLink href={`/staff/courses/${courseId}/assignments`}>
            Back to assignments
          </BackLink>
          <h1 className="text-2xl font-semibold tracking-tight">New Assignment</h1>
          <p className="text-muted-foreground mt-1">{courseId}</p>
        </div>

        <Card className="shadow-lg">
        <CardHeader>
          <CardTitle>Assignment details</CardTitle>
          <CardDescription>
            Create a new assignment shell. You can configure rubric, files, and artifacts
            on the setup page after creation.
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent className="space-y-4">
            {submitError && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">
                {submitError}
              </div>
            )}

            <div className="space-y-1">
              <label htmlFor="slug" className="text-xs font-semibold text-slate-500 uppercase">
                Slug
              </label>
              <Input
                id="slug"
                placeholder="e.g., lab-2-loops"
                aria-invalid={errors.slug ? true : undefined}
                {...register("slug", {
                  required: "Slug is required.",
                  pattern: {
                    value: SLUG_PATTERN,
                    message: "Use lowercase letters, numbers, and hyphens only.",
                  },
                })}
              />
              {errors.slug && (
                <p className="text-sm text-destructive">{errors.slug.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Used in URLs and must be unique within the course.
              </p>
            </div>

            <div className="space-y-1">
              <label htmlFor="title" className="text-xs font-semibold text-slate-500 uppercase">
                Title
              </label>
              <Input
                id="title"
                placeholder="e.g., Lab 2: Loops"
                aria-invalid={errors.title ? true : undefined}
                {...register("title", {
                  required: "Title is required.",
                  validate: (value) => value.trim().length > 0 || "Title is required.",
                })}
              />
              {errors.title && (
                <p className="text-sm text-destructive">{errors.title.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label htmlFor="language" className="text-xs font-semibold text-slate-500 uppercase">
                Language
              </label>
              <Controller
                name="language"
                control={control}
                rules={{ required: "Language is required." }}
                render={({ field }) => (
                  <Select value={field.value} disabled onValueChange={field.onChange}>
                    <SelectTrigger
                      id="language"
                      className="w-full"
                      aria-invalid={errors.language ? true : undefined}
                    >
                      <SelectValue placeholder="Select a language" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="python">Python</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.language && (
                <p className="text-sm text-destructive">{errors.language.message}</p>
              )}
            </div>

            <div className="space-y-1">
              <label htmlFor="canvas_ref" className="text-xs font-semibold text-slate-500 uppercase">
                Canvas reference (optional)
              </label>
              <Input
                id="canvas_ref"
                placeholder="e.g., canvas:lab-2"
                {...register("canvas_ref")}
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="module_id" className="text-xs font-semibold text-slate-500 uppercase">
                Module Assignment (optional)
              </label>
              <Controller
                name="module_id"
                control={control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="module_id" className="w-full">
                      <SelectValue placeholder="No Module" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Module</SelectItem>
                      {courseModules.map((m) => (
                        <SelectItem key={m.id} value={String(m.id)}>
                          {m.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>

            <div className="mb-3 flex items-center gap-2 pt-2">
              <input
                id="sandbox_enabled"
                type="checkbox"
                className="size-4 rounded border border-input"
                {...register("sandbox_enabled")}
              />
              <label htmlFor="sandbox_enabled" className="text-sm">
                Enable sandbox for students
              </label>
            </div>
          </CardContent>

          <CardFooter className="justify-end gap-2">
            <Button type="button" variant="outline" asChild>
              <Link href={`/staff/courses/${courseId}/assignments`}>Cancel</Link>
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create assignment and move to grading setup"}
            </Button>
          </CardFooter>
        </form>
        </Card>
      </div>
    </div>
  );
}
