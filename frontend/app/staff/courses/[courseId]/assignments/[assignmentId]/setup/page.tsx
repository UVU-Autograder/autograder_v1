"use client";

import { use, useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeftIcon, SaveIcon, ShieldAlertIcon, CheckCircle2Icon, PlayIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api-client";

type ScoringItem = {
  key: string;
  label: string;
  points: number;
  extra_credit: boolean;
  item_type: "pytest" | "manual";
  pytest_marker: string | null;
  rubric_group_key: string | null;
};

type ArtifactMetadata = {
  artifact_key: string;
  artifact_type: string;
  display_filename: string | null;
  size_bytes: number | null;
};

type FileRequirementConfig = {
  key: string;
  label: string | null;
  requirement_type: "exact" | "one_of" | "optional" | "pattern";
  paths: string[];
};

type RubricGroupConfig = {
  key: string;
  label: string;
  item_keys: string[];
};

type CompletionRequirementConfig = {
  key: string;
  label: string;
  test_keys: string[];
  minimum_passed: number;
};

type AssignmentConfigV1 = {
  schema_version: number;
  bundle: {
    required_files: string[];
    entrypoint: string;
    file_requirements?: FileRequirementConfig[];
  };
  concepts: {
    additions: string[];
  };
  artifacts: Record<string, { type: string; display_filename?: string }>;
  tests: { key: string; label: string; points: number; extra_credit: boolean; rubric_group_key?: string | null }[];
  rubric_groups?: RubricGroupConfig[];
  completion_requirements?: CompletionRequirementConfig[];
  manual_rubric_items?: { key: string; label: string; points: number; extra_credit: boolean; rubric_group_key?: string | null }[];
};

type StaffAssignmentSetup = {
  course_id: string;
  assignment_id: string;
  title: string;
  language: string;
  sandbox_enabled: boolean;
  base_points: number;
  extra_credit_points: number;
  required_files: string[];
  entrypoint_path: string;
  concept_additions: string[];
  scoring_items: ScoringItem[];
  artifacts: ArtifactMetadata[];
  config_json: AssignmentConfigV1;
};

type ValidationStatus = {
  status: "idle" | "queue" | "run" | "success" | "failure";
  errors: string[];
  score: number;
  max_score: number;
};

type PageProps = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

export default function SetupWizardPage({ params }: PageProps) {
  const { courseId, assignmentId } = use(params);
  const [setup, setSetup] = useState<StaffAssignmentSetup | null>(null);
  const [title, setTitle] = useState("");
  const [sandboxEnabled, setSandboxEnabled] = useState(false);
  const [scoringItems, setScoringItems] = useState<ScoringItem[]>([]);
  const [concepts, setConcepts] = useState<string[]>([]);
  
  // Validation states
  const [validation, setValidation] = useState<ValidationStatus>({
    status: "idle",
    errors: [],
    score: 0,
    max_score: 0,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        setIsLoading(true);
        setError(null);
      }
    });

    apiClient.get<StaffAssignmentSetup>(
      `/staff/courses/${courseId}/assignments/${assignmentId}/setup`
    ).then((data) => {
      if (active) {
        setSetup(data);
        setTitle(data.title);
        setSandboxEnabled(data.sandbox_enabled);
        setScoringItems(data.scoring_items);
        setConcepts(data.concept_additions);
        setIsLoading(false);
      }
    }).catch((err) => {
      if (active) {
        setError(err instanceof Error ? err.message : "Failed to load assignment config.");
        setIsLoading(false);
      }
    });

    return () => {
      active = false;
    };
  }, [courseId, assignmentId]);

  // Poll validation status if queued or running
  useEffect(() => {
    if (validation.status !== "queue" && validation.status !== "run") return;

    // eslint-disable-next-line prefer-const
    let timer: NodeJS.Timeout;
    const checkStatus = async () => {
      try {
        const data = await apiClient.get<ValidationStatus>(
          `/staff/courses/${courseId}/assignments/${assignmentId}/validation-status`
        );
        setValidation(data);
        if (data.status !== "queue" && data.status !== "run") {
          clearInterval(timer);
        }
      } catch {
        clearInterval(timer);
      }
    };

    timer = setInterval(checkStatus, 1500);
    return () => clearInterval(timer);
  }, [validation.status, courseId, assignmentId]);

  const handleSave = async () => {
    if (!setup) return;
    setIsSaving(true);
    setError(null);
    setSuccessMsg(null);

    // Reconstruct the config_json reflecting updates
    const updatedConfig = { ...setup.config_json };
    updatedConfig.concepts = { additions: concepts };
    
    // Map scoring items back to tests and manual_rubric_items
    updatedConfig.tests = scoringItems
      .filter((item) => item.item_type === "pytest")
      .map((item) => ({
        key: item.key,
        label: item.label,
        points: Number(item.points),
        extra_credit: item.extra_credit,
        rubric_group_key: item.rubric_group_key,
      }));

    updatedConfig.manual_rubric_items = scoringItems
      .filter((item) => item.item_type === "manual")
      .map((item) => ({
        key: item.key,
        label: item.label,
        points: Number(item.points),
        extra_credit: item.extra_credit,
        rubric_group_key: item.rubric_group_key,
      }));

    try {
      const data = await apiClient.put<StaffAssignmentSetup>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/setup`,
        {
          title,
          sandbox_enabled: sandboxEnabled,
          config_json: updatedConfig,
        }
      );
      setSetup(data);
      setTitle(data.title);
      setSandboxEnabled(data.sandbox_enabled);
      setScoringItems(data.scoring_items);
      setConcepts(data.concept_additions);
      setSuccessMsg("Configuration saved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update configuration.");
    } finally {
      setIsSaving(false);
    }
  };

  const handlePointChange = (key: string, val: string) => {
    setScoringItems((prev) =>
      prev.map((item) =>
        item.key === key ? { ...item, points: Math.max(0, parseInt(val) || 0) } : item
      )
    );
  };

  const handleConceptChange = (concept: string) => {
    setConcepts((prev) =>
      prev.includes(concept) ? prev.filter((c) => c !== concept) : [...prev, concept]
    );
  };

  const triggerValidation = async () => {
    setError(null);
    setValidation({
      status: "queue",
      errors: [],
      score: 0,
      max_score: 0,
    });

    try {
      await apiClient.post(
        `/staff/courses/${courseId}/assignments/${assignmentId}/validate-model-solution`,
        {}
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to trigger validation pipeline.");
      setValidation({
        status: "failure",
        errors: [err instanceof Error ? err.message : "Validation launch failed"],
        score: 0,
        max_score: 0,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading assignment details...</p>
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
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <div className="space-y-1">
            <Button variant="ghost" size="sm" className="-ml-3" asChild>
              <Link href={`/staff/courses/${courseId}`}>
                <ArrowLeftIcon className="mr-1 size-4" /> Back to course details
              </Link>
            </Button>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">Grading Setup</h1>
            <p className="text-slate-500">Configure parameters for {assignmentId}</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link href={`/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`}>
                Manage Artifacts
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href={`/staff/courses/${courseId}/assignments/${assignmentId}/runs`}>
                Official Runs
              </Link>
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              <SaveIcon className="mr-2 size-4" /> Save Setup
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
            {error}
          </div>
        )}
        {successMsg && (
          <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-600">
            {successMsg}
          </div>
        )}

        <Tabs defaultValue="general" className="w-full">
          <TabsList className="grid w-full grid-cols-4 lg:w-[480px] mb-6">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="scoring">Scoring</TabsTrigger>
            <TabsTrigger value="concepts">Concepts Whitelist</TabsTrigger>
            <TabsTrigger value="validation">Preflight Validation</TabsTrigger>
          </TabsList>

          <TabsContent value="general">
            <Card>
              <CardHeader>
                <CardTitle>General Config</CardTitle>
                <CardDescription>
                  Modify basic assignment properties and sandbox permissions.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Assignment Title</label>
                    <Input value={title} onChange={(e) => setTitle(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Language</label>
                    <Input value={setup?.language} disabled />
                  </div>
                </div>

                <div className="flex items-center space-x-2 pt-2">
                  <input
                    type="checkbox"
                    id="sandbox"
                    checked={sandboxEnabled}
                    onChange={(e) => setSandboxEnabled(e.target.checked)}
                    className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="sandbox" className="text-sm font-medium text-slate-700">
                    Enable Student Sandbox (zero-retention testing environment)
                  </label>
                </div>

                <div className="border-t border-slate-200 pt-4 mt-6">
                  <h3 className="font-semibold text-slate-800 mb-2">Internal Zip Bundle Specs</h3>
                  <p className="text-xs text-slate-500 mb-3">
                    Derived from the initial config payload uploaded to storage.
                  </p>
                  <div className="space-y-1 text-sm text-slate-700">
                    <p>
                      <span className="font-medium text-slate-600">Entrypoint:</span>{" "}
                      {setup?.entrypoint_path}
                    </p>
                    <p>
                      <span className="font-medium text-slate-600">Required Files:</span>{" "}
                      {setup?.required_files.join(", ")}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="scoring">
            <Card>
              <CardHeader>
                <CardTitle>Scoring Rubric Items</CardTitle>
                <CardDescription>
                  Assign point allocations to unit test checks and manual evaluations.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {scoringItems.map((item) => (
                    <div
                      key={item.key}
                      className="flex flex-col gap-4 border-b border-slate-100 pb-4 md:flex-row md:items-center md:justify-between"
                    >
                      <div className="space-y-1">
                        <p className="font-semibold text-slate-800">{item.label}</p>
                        <p className="text-xs text-slate-400">
                          Key: {item.key} | Type: {item.item_type}
                        </p>
                      </div>
                      <div className="flex items-center gap-4">
                        {item.extra_credit && (
                          <span className="rounded bg-indigo-50 px-2 py-0.5 text-xs font-bold text-indigo-600">
                            Extra Credit
                          </span>
                        )}
                        <div className="flex items-center gap-2">
                          <label className="text-sm font-medium text-slate-500">Points</label>
                          <Input
                            type="number"
                            className="w-20"
                            value={item.points}
                            onChange={(e) => handlePointChange(item.key, e.target.value)}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="concepts">
            <Card>
              <CardHeader>
                <CardTitle>Concepts Covered Whitelist</CardTitle>
                <CardDescription>
                  Determine allowed syntactic structures. Flag deviations as warnings.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-slate-800 mb-2">Assignment Additions</h3>
                    <p className="text-xs text-slate-500 mb-3">
                      Select extra programming concepts specific to this assignment:
                    </p>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                      {allPossibleConcepts.map((concept) => (
                        <div key={concept} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id={`concept-${concept}`}
                            checked={concepts.includes(concept)}
                            onChange={() => handleConceptChange(concept)}
                            className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <label
                            htmlFor={`concept-${concept}`}
                            className="text-sm font-medium text-slate-700 uppercase"
                          >
                            {concept}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="validation">
            <Card>
              <CardHeader>
                <CardTitle>Preflight Validation Pipeline</CardTitle>
                <CardDescription>
                  Execute model solutions against the config suite. Ensure test parity.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Button onClick={triggerValidation} disabled={validation.status === "queue" || validation.status === "run"}>
                    <PlayIcon className="mr-2 size-4" /> Run Preflight Validation
                  </Button>
                </div>

                {validation.status !== "idle" && (
                  <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-900">Validation Run Status</h4>
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-bold uppercase ${
                          validation.status === "success"
                            ? "bg-green-50 text-green-700"
                            : validation.status === "failure"
                              ? "bg-red-50 text-red-700"
                              : "bg-amber-50 text-amber-700 animate-pulse"
                        }`}
                      >
                        {validation.status}
                      </span>
                    </div>

                    {(validation.status === "queue" || validation.status === "run") && (
                      <p className="text-sm text-slate-500 animate-pulse">
                        Pipeline executing in Sandbox Kata container. Polling results...
                      </p>
                    )}

                    {validation.status === "success" && (
                      <div className="space-y-2">
                        <div className="flex items-center text-green-700 gap-1.5 text-sm font-semibold">
                          <CheckCircle2Icon className="size-4" /> Parity Confirmed. Model Solution scored {validation.score} / {validation.max_score}.
                        </div>
                      </div>
                    )}

                    {validation.status === "failure" && (
                      <div className="space-y-2">
                        <div className="flex items-center text-red-700 gap-1.5 text-sm font-semibold">
                          <ShieldAlertIcon className="size-4" /> Pipeline validation failures found:
                        </div>
                        <ul className="list-disc pl-5 text-sm text-slate-600 space-y-1">
                          {validation.errors.map((err, idx) => (
                            <li key={idx}>{err}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
