"use client";

import { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { PlayIcon } from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";

type IngestionResponse = {
  run_id: string;
  status: string;
  workflow_type: string;
  total_submission_count: number;
  created_at: string;
};

type RunStatusResponse = {
  run_id: string;
  state: "queue" | "run" | "complete" | "failure";
  queue_position: number | null;
  eta_band: string | null;
  message: string | null;
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

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

export default function RunsPage({ params }: PageProps) {
  const router = useRouter();
  const { courseId, assignmentId } = use(params);
  const [sections, setSections] = useState<StaffSection[]>([]);
  const [sectionId, setSectionId] = useState<string>("");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [activeStatus, setActiveStatus] = useState<RunStatusResponse | null>(null);
  const [zipFile, setZipFile] = useState<File | null>(null);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
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

    apiClient.get<StaffSectionListResponse>(`/staff/courses/${courseId}/sections`)
      .then((sectionsData) => {
        if (!active) return;
        setSections(sectionsData.sections);
        if (sectionsData.sections.length === 1) {
          setSectionId(String(sectionsData.sections[0].id));
        }
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

  // Poll status of an active running process
  useEffect(() => {
    if (!activeRunId) return;

    const checkStatus = async () => {
      try {
        const data = await apiClient.get<RunStatusResponse>(`/runs/${activeRunId}/status`);
        setActiveStatus(data);
        if (data.state === "complete" || data.state === "failure") {
          clearInterval(timer);
          setSuccess("Grading run processing complete! Redirecting to results...");
          const runIdToRedirect = activeRunId;
          setActiveRunId(null);
          setTimeout(() => {
            router.push(`/staff/courses/${courseId}/assignments/${assignmentId}/runs/${runIdToRedirect}`);
          }, 1000);
        }
      } catch {
        clearInterval(timer);
      }
    };

    const timer = setInterval(checkStatus, 2000);
    return () => clearInterval(timer);
  }, [activeRunId, courseId, assignmentId, router]);

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
    setSuccess(null);

    const formData = new FormData();
    formData.append("file", zipFile);
    formData.append("section_id", sectionId);

    try {
      const res = await apiClient.postForm<IngestionResponse>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/submissions/ingest`,
        formData
      );
      setZipFile(null);
      setActiveRunId(res.data.run_id);
      setActiveStatus({
        run_id: res.data.run_id,
        state: "queue",
        queue_position: null,
        eta_band: null,
        message: "Ingestion accepted. Queued for execution...",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "ZIP Ingestion failed.");
    } finally {
      setIsUploading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading runs history...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 space-y-1">
          <BackLink href={`/staff/courses/${courseId}/assignments/${assignmentId}`} variant="compact">
            Back to assignment
          </BackLink>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Official Canvas Runs</h1>
          <p className="text-slate-500">Launch student grading cycles via Canvas ZIP exports.</p>
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

        <div className="mx-auto max-w-xl space-y-4">
          {/* Launch Panel */}
          <Card>
            <form onSubmit={handleIngest}>
              <CardHeader>
                <CardTitle className="text-lg">Launch New Run</CardTitle>
                <CardDescription>Upload a standard ZIP containing Canvas assignments.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500" htmlFor="section">
                    Section
                  </label>
                  <select
                    id="section"
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
                    value={sectionId}
                    required
                    onChange={(e) => setSectionId(e.target.value)}
                  >
                    <option value="" disabled>
                      Select a section
                    </option>
                    {sections.map((section) => (
                      <option key={section.id} value={section.id}>
                        CRN {section.crn}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500">Submissions ZIP</label>
                  <input
                    type="file"
                    accept=".zip"
                    className="w-full text-xs text-slate-500 file:mr-2 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-slate-700 hover:file:bg-slate-200"
                    required
                    onChange={(e) => setZipFile(e.target.files?.[0] || null)}
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isUploading || !!activeRunId || !sectionId}
                >
                  <PlayIcon className="mr-2 size-4" />
                  {isUploading ? "Uploading ZIP..." : "Launch grading run"}
                </Button>
              </CardFooter>
            </form>
          </Card>

          {activeStatus && (
            <Card className="border-amber-200 bg-amber-50">
              <CardHeader>
                <CardTitle className="text-sm text-amber-800">Processing Active Run</CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-amber-700 space-y-2">
                <p>
                  <span className="font-semibold">Run ID:</span> {activeStatus.run_id}
                </p>
                <p>
                  <span className="font-semibold">State:</span>{" "}
                  <span className="uppercase font-bold">{activeStatus.state}</span>
                </p>
                {activeStatus.queue_position !== null && (
                  <p>
                    <span className="font-semibold">Queue Position:</span>{" "}
                    {activeStatus.queue_position}
                  </p>
                )}
                {activeStatus.message && (
                  <p className="mt-1 border-t border-amber-200 pt-2 italic">
                    {activeStatus.message}
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
