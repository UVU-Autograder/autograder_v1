"use client";

import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { PlayIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api-client";

type IngestionResponse = {
  run_id: string;
  status: string;
  workflow_type: string;
  total_submission_count: number;
  created_at: string;
};

type StaffSection = {
  id: number;
  crn: string;
  is_active: boolean;
};

type StaffSectionListResponse = {
  course_id: string;
  sections: StaffSection[];
};

type PreflightResponse = {
  passed: boolean;
  errors: string[];
};

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

export default function RunsPage({ params }: PageProps) {
  const router = useRouter();
  const { courseId, assignmentId } = use(params);
  const [sections, setSections] = useState<StaffSection[]>([]);
  const [sectionId, setSectionId] = useState<string>("");
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [preflight, setPreflight] = useState<PreflightResponse | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        setIsLoading(true);
        setError(null);
      }
    });

    Promise.all([
      apiClient.get<StaffSectionListResponse>(
        `/staff/courses/${courseId}/sections`,
      ),
      apiClient.post<PreflightResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/validate`,
        {},
      ),
    ])
      .then(([sectionsData, preflightData]) => {
        if (!active) return;
        setSections(sectionsData.sections);
        if (sectionsData.sections.length === 1) {
          setSectionId(String(sectionsData.sections[0].id));
        }
        setPreflight(preflightData);
        setIsLoading(false);
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Failed to load runs.");
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [courseId, assignmentId]);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sectionId) {
      setError("Please select a course section.");
      return;
    }
    if (!zipFile) {
      setError("Please select a Canvas ZIP export file.");
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", zipFile);
    formData.append("section_id", sectionId);

    try {
      const res = await apiClient.postForm<IngestionResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/submissions/ingest`,
        formData,
      );
      setZipFile(null);
      router.push(
        `/staff/courses/${courseId}/assignments/${assignmentId}/runs/${res.data.run_id}`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "ZIP Ingestion failed.");
      setIsUploading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <p className="text-muted-foreground font-medium animate-pulse">
          Loading runs...
        </p>
      </div>
    );
  }

  const preflightBlocked = preflight !== null && !preflight.passed;

  return (
    <div className="min-h-screen bg-background p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 space-y-1">
          <BackLink
            href={`/staff/courses/${courseId}/assignments/${assignmentId}`}
            variant="compact"
          >
            Back to assignment
          </BackLink>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Grading Runs
          </h1>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive font-medium">
            {error}
          </div>
        )}

        <div className="mx-auto max-w-xl space-y-4">
          {preflight && (
            <div
              className={`rounded-lg border p-3 text-sm ${
                preflight.passed
                  ? "border-success/30 bg-success/10 text-success"
                  : "border-destructive/30 bg-destructive/10 text-destructive"
              }`}
            >
              {preflight.passed ? (
                <p className="font-medium">Assignment ready to grade</p>
              ) : (
                <div className="space-y-1">
                  <p className="font-medium">
                    Assignment is not ready to grade
                  </p>
                  {preflight.errors.slice(0, 2).map((msg) => (
                    <p key={msg} className="text-xs opacity-90">
                      {msg}
                    </p>
                  ))}
                  <Link
                    href={`/staff/courses/${courseId}/assignments/${assignmentId}`}
                    className="inline-block text-xs font-semibold underline underline-offset-2"
                  >
                    Open assignment setup
                  </Link>
                </div>
              )}
            </div>
          )}

          <p className="text-sm text-muted-foreground">Review access and downloads end 23 hours after upload. Export results before that deadline; automatic deletion then begins.</p>
          <Card>
            <form onSubmit={handleIngest}>
              <CardHeader>
                <CardTitle className="text-lg">Launch New Run</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="section" className="text-xs">
                    Section
                  </Label>
                  <select
                    id="section"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
                    value={sectionId}
                    required
                    onChange={(e) => setSectionId(e.target.value)}
                  >
                    <option
                      value=""
                      disabled
                      className="bg-background text-foreground"
                    >
                      Select a section
                    </option>
                    {sections.map((section) => (
                      <option
                        key={section.id}
                        value={section.id}
                        className="bg-background text-foreground"
                      >
                        CRN {section.crn}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="submissions-zip-input" className="text-xs">
                    Submissions ZIP
                  </Label>
                  <input
                    id="submissions-zip-input"
                    type="file"
                    accept=".zip"
                    className="w-full text-xs text-muted-foreground file:mr-2 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-foreground hover:file:bg-muted/80"
                    required
                    onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isUploading || !sectionId || preflightBlocked}
                >
                  <PlayIcon className="mr-2 size-4" />
                  {isUploading ? "Uploading ZIP..." : "Launch grading run"}
                </Button>
              </CardContent>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
