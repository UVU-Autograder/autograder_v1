"use client";

import React, { use, useCallback, useEffect, useState, Fragment } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  SaveIcon,
  ShieldAlertIcon,
  CheckCircle2Icon,
  PlayIcon,
  PlusIcon,
  Trash2Icon,
  XIcon,
  HelpCircleIcon,
  PlusCircleIcon,
  FileTextIcon,
  CopyIcon,
  CheckIcon,
} from "lucide-react";
import { BackLink } from "@/components/back-link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api-client";
import { slugifyKey } from "@/lib/slugify";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import MonacoEditor from "@/components/monaco-editor";
import {
  getConceptsMetadata,
  deleteStaffAssignment,
} from "@/features/assignments/api";
import { ConceptMetadata } from "@/features/assignments/types";

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
  label: string;
  paths?: string[] | null;
  pattern?: string | null;
};

type ScoringItemConfig = {
  key: string;
  label: string;
  points: number;
  extra_credit: boolean;
  item_type?: "pytest" | "manual";
  rubric_group_key?: string | null;
  inputs?: string[] | null;
  outputs?: string[] | null;
};

type ManualRubricItemConfig = ScoringItemConfig;

type RubricGroupConfig = {
  key: string;
  label: string;
};

type CompletionRequirementConfig = {
  key: string;
  label: string;
  test_keys: string[];
  minimum_passed: number;
};

type AssignmentConfigV1 = {
  bundle: {
    entrypoint: string;
    file_requirements?: FileRequirementConfig[];
  };
  concepts: {
    additions: string[];
  };
  artifacts: Record<string, { type: string; display_filename?: string }>;
  scoring_items: ScoringItemConfig[];
  rubric_groups?: RubricGroupConfig[];
  completion_requirements?: CompletionRequirementConfig[];
  dependencies?: string[];
};

type StaffAssignmentSetup = {
  course_id: string;
  assignment_id: string;
  title: string;
  language: string;
  module_id: number | null;
  sandbox_enabled: boolean;
  base_points: number;
  extra_credit_points: number;
  entrypoint_path: string;
  concept_additions: string[];
  scoring_items: ScoringItem[];
  artifacts: ArtifactMetadata[];
  config_json: AssignmentConfigV1;
  effective_allowed_concepts?: string[];
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

type CourseConceptsResponse = {
  modules: { id: number; name: string }[];
};

const TEST_KEY_RE = /^[a-z][a-z0-9_]*$/;
const DEPENDENCY_RE = /^[A-Za-z0-9_.-]+$/;

// Reusable tag list badge component
type TagBadgeListProps = {
  tags: string[];
  onRemove: (tag: string) => void;
  emptyText: string;
};

function TagBadgeList({ tags, onRemove, emptyText }: TagBadgeListProps) {
  return (
    <div className="flex flex-wrap gap-2 mb-3">
      {tags.map((tag) => (
        <span
          key={tag}
          className="inline-flex items-center gap-1 bg-slate-100 text-slate-800 text-xs font-mono px-2 py-1 rounded border border-slate-200"
        >
          {tag}
          <button
            type="button"
            onClick={() => onRemove(tag)}
            className="text-slate-400 hover:text-red-500 transition-colors cursor-pointer"
          >
            <XIcon className="size-3" />
          </button>
        </span>
      ))}
      {tags.length === 0 && (
        <span className="text-xs text-slate-400 italic">{emptyText}</span>
      )}
    </div>
  );
}

type ScoringTableItem = {
  key: string;
  label: string;
  points: number;
  extra_credit: boolean;
  rubric_group_key?: string | null;
  inputs?: string[] | null;
};

// Reusable Scoring Items Table component
type ScoringItemsTableProps<T extends ScoringTableItem> = {
  items: T[];
  onUpdate: (key: string, field: keyof T, val: unknown) => void;
  onDelete: (key: string) => void;
  rubricGroups: RubricGroupConfig[];
  title: string;
  description: string;
  addButtonLabel: string;
  onAdd: () => void;
  emptyText: string;
  renderDetails?: (item: T) => React.ReactNode;
};

function ScoringItemsTable<T extends ScoringTableItem>({
  items,
  onUpdate,
  onDelete,
  rubricGroups,
  title,
  description,
  addButtonLabel,
  onAdd,
  emptyText,
  renderDetails,
}: ScoringItemsTableProps<T>) {
  const [expandedKeys, setExpandedKeys] = useState<Record<string, boolean>>({});
  const [editingKeyMap, setEditingKeyMap] = useState<Record<string, boolean>>(
    {},
  );
  const colSpan = renderDetails ? 6 : 5;

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-sm font-bold text-slate-800">{title}</h3>
          <p className="text-xs text-slate-400">{description}</p>
        </div>
        <Button type="button" onClick={onAdd} variant="outline" size="sm">
          <PlusCircleIcon className="size-4 mr-1.5" /> {addButtonLabel}
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase">
              <th className="py-2 pr-2">Student-Facing Description</th>
              <th className="py-2 px-2 w-20">Points</th>
              <th className="py-2 px-2 w-24 text-center">Extra Credit?</th>
              <th className="py-2 px-2">Rubric Group</th>
              {renderDetails && (
                <th className="py-2 px-2 w-32 text-center">I/O Cases</th>
              )}
              <th className="py-2 pl-2 text-right">Delete</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => {
              const isExpanded = !!expandedKeys[item.key];
              const isEditingKey = !!editingKeyMap[item.key];
              return (
                <Fragment key={item.key}>
                  <tr className="hover:bg-slate-50/50">
                    <td className="py-2 pr-2">
                      <div className="space-y-1">
                        <Input
                          value={item.label}
                          onChange={(e) =>
                            onUpdate(
                              item.key,
                              "label" as keyof T,
                              e.target.value,
                            )
                          }
                          placeholder="e.g. Candy Class Hierarchy Intact"
                          className="text-xs h-8"
                        />
                        <div className="flex items-center justify-between text-[11px] text-slate-500">
                          <span className="font-mono text-slate-600">
                            Key:{" "}
                            <span className="font-semibold text-indigo-700">
                              {item.key}
                            </span>
                          </span>
                          <button
                            type="button"
                            onClick={() =>
                              setEditingKeyMap((prev) => ({
                                ...prev,
                                [item.key]: !prev[item.key],
                              }))
                            }
                            className="text-slate-400 hover:text-indigo-600 cursor-pointer text-[10px]"
                          >
                            {isEditingKey ? "Done" : "✏️ Edit key"}
                          </button>
                        </div>
                        {isEditingKey && (
                          <Input
                            value={item.key}
                            onChange={(e) =>
                              onUpdate(
                                item.key,
                                "key" as keyof T,
                                e.target.value,
                              )
                            }
                            className="font-mono text-[11px] h-6 border-indigo-300"
                          />
                        )}
                      </div>
                    </td>
                    <td className="py-2 px-2">
                      <Input
                        type="number"
                        value={item.points}
                        onChange={(e) =>
                          onUpdate(
                            item.key,
                            "points" as keyof T,
                            e.target.value,
                          )
                        }
                        className="w-16 h-8 text-xs text-center"
                      />
                    </td>
                    <td className="py-2 px-2 text-center">
                      <input
                        type="checkbox"
                        checked={item.extra_credit}
                        onChange={(e) =>
                          onUpdate(
                            item.key,
                            "extra_credit" as keyof T,
                            e.target.checked,
                          )
                        }
                        className="size-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                      />
                    </td>
                    <td className="py-2 px-2">
                      <select
                        value={item.rubric_group_key || ""}
                        onChange={(e) =>
                          onUpdate(
                            item.key,
                            "rubric_group_key" as keyof T,
                            e.target.value || null,
                          )
                        }
                        className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs focus:border-indigo-500 focus:outline-none h-8"
                      >
                        <option value="">-- None --</option>
                        {rubricGroups.map((g) => (
                          <option key={g.key} value={g.key}>
                            {g.label || g.key}
                          </option>
                        ))}
                      </select>
                    </td>
                    {renderDetails && (
                      <td className="py-2 px-2 text-center">
                        <Button
                          type="button"
                          variant={isExpanded ? "secondary" : "outline"}
                          size="sm"
                          onClick={() =>
                            setExpandedKeys((prev) => ({
                              ...prev,
                              [item.key]: !prev[item.key],
                            }))
                          }
                          className="text-xs h-7 px-2 font-mono whitespace-nowrap"
                        >
                          {isExpanded
                            ? "Hide I/O"
                            : `I/O Cases (${item.inputs?.length || 0})`}
                        </Button>
                      </td>
                    )}
                    <td className="py-2 pl-2 text-right">
                      <button
                        type="button"
                        onClick={() => onDelete(item.key)}
                        className="text-slate-400 hover:text-red-500 transition-colors p-1 cursor-pointer"
                      >
                        <Trash2Icon className="size-3.5" />
                      </button>
                    </td>
                  </tr>
                  {renderDetails && isExpanded && (
                    <tr className="bg-slate-50/40">
                      <td colSpan={colSpan} className="py-3 px-4">
                        {renderDetails(item)}
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
        {items.length === 0 && (
          <p className="text-xs text-slate-400 italic text-center py-4">
            {emptyText}
          </p>
        )}
      </div>
    </div>
  );
}

export default function SetupWizardPage({ params }: PageProps) {
  const router = useRouter();
  const { courseId, assignmentId } = use(params);
  const [setup, setSetup] = useState<StaffAssignmentSetup | null>(null);

  // Step 1
  const [title, setTitle] = useState("");
  const [sandboxEnabled, setSandboxEnabled] = useState(true);
  const [moduleId, setModuleId] = useState<number | null>(null);
  const [courseModules, setCourseModules] = useState<
    { id: number; name: string }[]
  >([]);

  // Step 2
  const [requiredFiles, setRequiredFiles] = useState<string[]>([]);
  const [entrypoint, setEntrypoint] = useState("");
  const [newRequiredFile, setNewRequiredFile] = useState("");
  const [fileRequirements, setFileRequirements] = useState<
    FileRequirementConfig[]
  >([]);

  // Step 3
  const [tests, setTests] = useState<ScoringItemConfig[]>([]);
  const [manualRubricItems, setManualRubricItems] = useState<
    ManualRubricItemConfig[]
  >([]);
  const [rubricGroups, setRubricGroups] = useState<RubricGroupConfig[]>([]);

  // Step 4
  const [concepts, setConcepts] = useState<string[]>([]);
  const [conceptMeta, setConceptMeta] = useState<
    Record<string, ConceptMetadata>
  >({});

  // Step 5
  const [dependencies, setDependencies] = useState<string[]>([]);
  const [newDependency, setNewDependency] = useState("");

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

  // Code Editor states
  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [isLoadingCode, setIsLoadingCode] = useState(false);
  const [editArtifactKey, setEditArtifactKey] = useState("");
  const [editArtifactType, setEditArtifactType] = useState("");
  const [editArtifactFilename, setEditArtifactFilename] = useState("");
  const [editCodeText, setEditCodeText] = useState("");
  const [isSavingCode, setIsSavingCode] = useState(false);
  const [codeEditorError, setCodeEditorError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Auto-derivation custom key tracking states
  const [customFileReqKeys, setCustomFileReqKeys] = useState<
    Record<number, boolean>
  >({});
  const [customTestKeys, setCustomTestKeys] = useState<Record<string, boolean>>(
    {},
  );
  const [customManualKeys, setCustomManualKeys] = useState<
    Record<string, boolean>
  >({});
  const [editingKeyItem, setEditingKeyItem] = useState<string | null>(null);

  const handleCopyStudentLink = () => {
    const studentLink = `${window.location.origin}/sandbox/${courseId}/assignments/${assignmentId}`;
    navigator.clipboard
      .writeText(studentLink)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch((err) => {
        console.error("Failed to copy link: ", err);
      });
  };

  // Centralized State Initialization Helper
  const syncSetupState = useCallback(
    (data: StaffAssignmentSetup, meta: Record<string, ConceptMetadata>) => {
      const config = data.config_json;
      setSetup(data);
      setTitle(data.title);
      setSandboxEnabled(data.sandbox_enabled);
      setModuleId(data.module_id !== undefined ? data.module_id : null);

      // Step 2
      const initialEntrypoint = config.bundle?.entrypoint || "";
      const initialReqs = config.bundle?.file_requirements || [];

      setEntrypoint(initialEntrypoint);
      setFileRequirements(initialReqs);

      // Step 3
      if (config.scoring_items) {
        setTests(config.scoring_items.filter((item) => (item.item_type || "pytest") === "pytest"));
        setManualRubricItems(config.scoring_items.filter((item) => item.item_type === "manual"));
      } else {
        setTests([]);
        setManualRubricItems([]);
      }
      setRubricGroups(config.rubric_groups || []);

      // Step 4
      const additions = config.concepts?.additions || [];
      const predefined = Object.keys(meta);
      setConcepts(additions.filter((c) => predefined.includes(c)));

      // Step 5
      setDependencies(config.dependencies || []);
    },
    [],
  );

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (active) {
        setIsLoading(true);
        setError(null);
      }
    });

    Promise.all([
      apiClient.get<StaffAssignmentSetup>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/setup`,
      ),
      getConceptsMetadata(),
      apiClient.get<CourseConceptsResponse>(
        `/staff/courses/${courseId}/concepts`,
      ),
    ])
      .then(([setupData, metaData, courseConcepts]) => {
        if (active) {
          setConceptMeta(metaData);
          setCourseModules(courseConcepts.modules || []);
          syncSetupState(setupData, metaData);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load assignment config.",
          );
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [courseId, assignmentId, syncSetupState]);

  // Poll validation status if queued or running
  useEffect(() => {
    if (validation.status !== "queue" && validation.status !== "run") return;

    const checkStatus = async () => {
      try {
        const data = await apiClient.get<ValidationStatus>(
          `/staff/courses/${courseId}/assignments/${assignmentId}/validation-status`,
        );
        setValidation(data);
        if (data.status !== "queue" && data.status !== "run") {
          clearInterval(timer);
        }
      } catch {
        clearInterval(timer);
      }
    };

    const timer = setInterval(checkStatus, 1500);
    return () => clearInterval(timer);
  }, [validation.status, courseId, assignmentId]);

  const sanitizeKey = (val: string) => {
    return val.toLowerCase().replace(/[^a-z0-9_]/g, "_");
  };

  const isValidKey = (key: string) => TEST_KEY_RE.test(key);
  const isValidDependency = (dep: string) => DEPENDENCY_RE.test(dep);

  const getClientValidationErrors = () => {
    const errors: string[] = [];

    // Title
    if (!title.trim()) {
      errors.push("Assignment Title is required.");
    }

    // Entrypoint
    if (!entrypoint.trim()) {
      errors.push("Entrypoint path is required.");
    }

    const allTestKeys = tests.map((t) => t.key);
    const allManualKeys = manualRubricItems.map((m) => m.key);
    const allGroupKeys = rubricGroups.map((g) => g.key);

    // Generic list key validation
    const validateKeyList = (keys: string[], listName: string) => {
      keys.forEach((k) => {
        if (!k.trim()) errors.push(`${listName} key cannot be empty.`);
        else if (!isValidKey(k)) {
          errors.push(
            `${listName} key "${k}" is invalid. Must start with a lowercase letter and contain only lowercase letters, numbers, and underscores.`,
          );
        }
      });
    };

    validateKeyList(allTestKeys, "Test");
    validateKeyList(allManualKeys, "Manual Rubric Item");
    validateKeyList(allGroupKeys, "Rubric Group");

    // Duplicates
    const checkDuplicates = (keys: string[], name: string) => {
      const duplicates = keys.filter((k, idx) => keys.indexOf(k) !== idx);
      if (duplicates.length > 0) {
        errors.push(
          `Duplicate keys found in ${name}: ${Array.from(new Set(duplicates)).join(", ")}`,
        );
      }
    };

    checkDuplicates(allTestKeys, "Tests");
    checkDuplicates(allManualKeys, "Manual Rubric Items");
    checkDuplicates(allGroupKeys, "Rubric Groups");

    // Tests & Manual overlap
    const overlap = allTestKeys.filter((k) => allManualKeys.includes(k));
    if (overlap.length > 0) {
      errors.push(
        `Scoring item keys overlap between Tests and Manual Rubric Items: ${overlap.join(", ")}`,
      );
    }

    // File Requirements validation
    fileRequirements.forEach((req, idx) => {
      if (!req.label || !req.label.trim()) {
        errors.push(`File requirement #${idx + 1} must have a label.`);
      }
      if (req.pattern !== undefined && req.pattern !== null) {
        if (!req.pattern.trim()) {
          errors.push(
            `File requirement "${req.label || idx + 1}" (glob pattern) cannot be blank.`,
          );
        }
      } else {
        const validPaths = (req.paths || []).filter((p) => p.trim());
        if (validPaths.length === 0) {
          errors.push(
            `File requirement "${req.label || idx + 1}" must have at least one non-empty path.`,
          );
        }
      }
    });

    // Entrypoint verification against paths requirements
    const knownPaths = new Set<string>();
    fileRequirements.forEach((req) => {
      if (req.paths) {
        req.paths.forEach((p) => {
          if (p.trim()) knownPaths.add(p.trim());
        });
      }
    });

    if (knownPaths.size > 0 && entrypoint && !knownPaths.has(entrypoint)) {
      errors.push(
        `Entrypoint "${entrypoint}" is not present in any file requirement paths list.`,
      );
    }

    // Dependencies
    dependencies.forEach((dep) => {
      if (!isValidDependency(dep)) {
        errors.push(
          `Dependency "${dep}" contains invalid characters. Allowed: alphanumeric, underscores, hyphens, and periods.`,
        );
      }
    });

    return errors;
  };

  const handleSave = async () => {
    if (!setup) return;
    setIsSaving(true);
    setError(null);
    setSuccessMsg(null);

    const clientErrors = getClientValidationErrors();
    if (clientErrors.length > 0) {
      setError(
        `Please resolve the following errors before saving:\n${clientErrors.join("\n")}`,
      );
      setIsSaving(false);
      return;
    }

    // Rubric groups stored as { key, label }
    const updatedRubricGroups = rubricGroups.map((group) => ({
      key: group.key,
      label: group.label,
    }));

    // Sync renamed test keys in completion requirements
    const keyMap: Record<string, string> = {};
    if (setup.config_json.scoring_items) {
      const origPytests = setup.config_json.scoring_items.filter(
        (item) => (item.item_type || "pytest") === "pytest",
      );
      origPytests.forEach((origTest, idx) => {
        const currentTest = tests[idx];
        if (currentTest && origTest.key !== currentTest.key) {
          keyMap[origTest.key] = currentTest.key;
        }
      });
    }

    const updatedCompletionRequirements = (
      setup.config_json.completion_requirements || []
    ).map((req) => {
      const updatedTestKeys = req.test_keys.map((tk) => keyMap[tk] || tk);
      return {
        ...req,
        test_keys: updatedTestKeys,
      };
    });

    // Reconstruct the config_json reflecting updates
    const updatedConfig: AssignmentConfigV1 = {
      ...setup.config_json,
      bundle: {
        entrypoint: entrypoint,
        file_requirements: fileRequirements,
      },
      concepts: {
        additions: concepts,
      },
      scoring_items: [
        ...tests.map((t) => ({
          key: t.key,
          label: t.label,
          points: Number(t.points),
          extra_credit: t.extra_credit,
          item_type: "pytest" as const,
          rubric_group_key: t.rubric_group_key || null,
          inputs: t.inputs || null,
          outputs: t.outputs || null,
        })),
        ...manualRubricItems.map((m) => ({
          key: m.key,
          label: m.label,
          points: Number(m.points),
          extra_credit: m.extra_credit,
          item_type: "manual" as const,
          rubric_group_key: m.rubric_group_key || null,
        })),
      ],
      rubric_groups: updatedRubricGroups,
      completion_requirements: updatedCompletionRequirements,
      dependencies: dependencies,
    };

    try {
      const data = await apiClient.put<StaffAssignmentSetup>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/setup`,
        {
          title,
          sandbox_enabled: sandboxEnabled,
          module_id: moduleId,
          config_json: updatedConfig,
        },
      );
      syncSetupState(data, conceptMeta);
      setSuccessMsg("Configuration saved successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update configuration.",
      );
    } finally {
      setIsSaving(false);
    }
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
        {},
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to trigger validation pipeline.",
      );
      setValidation({
        status: "failure",
        errors: [
          err instanceof Error ? err.message : "Validation launch failed",
        ],
        score: 0,
        max_score: 0,
      });
    }
  };

  const fetchArtifactText = async (key: string): Promise<string> => {
    const token =
      localStorage.getItem("token") || sessionStorage.getItem("token");
    const baseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
    const url = `${baseUrl.replace(/\/$/, "")}/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${key}`;
    const headers: Record<string, string> = {};
    if (token) {
      headers["authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(url, { headers });
    if (!res.ok) {
      throw new Error(`Failed to fetch artifact content: ${res.statusText}`);
    }
    return res.text();
  };

  const openCodeEditor = async (
    key: string,
    type: string,
    filename: string,
  ) => {
    setError(null);
    setCodeEditorError(null);
    setEditArtifactKey(key);
    setEditArtifactType(type);
    setEditArtifactFilename(filename);
    setEditCodeText("");
    setIsCodeModalOpen(true);
    setIsLoadingCode(true);
    setIsSavingCode(false);

    try {
      const text = await fetchArtifactText(key);
      setEditCodeText(text);
      setIsLoadingCode(false);
    } catch (err) {
      setCodeEditorError(
        err instanceof Error ? err.message : "Failed to load artifact code.",
      );
      setIsLoadingCode(false);
    }
  };

  const saveCodeChanges = async () => {
    if (!editArtifactKey) return;
    setIsSavingCode(true);
    setCodeEditorError(null);

    const file = new File([editCodeText], editArtifactFilename, {
      type: "text/plain",
    });
    const formData = new FormData();
    formData.append("file", file);
    formData.append("artifact_key", editArtifactKey);
    formData.append("artifact_type", editArtifactType);

    try {
      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData,
      );
      setIsCodeModalOpen(false);
      setSuccessMsg(`Code saved successfully for '${editArtifactFilename}'.`);
      apiClient
        .get<StaffAssignmentSetup>(
          `/staff/courses/${courseId}/assignments/${assignmentId}/setup`,
        )
        .then((data) => {
          setSetup(data);
        })
        .catch(() => {});
    } catch (err) {
      setCodeEditorError(
        err instanceof Error ? err.message : "Failed to save code changes.",
      );
    } finally {
      setIsSavingCode(false);
    }
  };

  // Helper selectors for entrypoint options
  const getEntrypointOptions = () => {
    const options = new Set<string>();
    fileRequirements.forEach((req) => {
      if (req.paths) {
        req.paths.forEach((p) => {
          if (p.trim()) options.add(p.trim());
        });
      }
    });
    if (entrypoint && entrypoint.trim()) {
      options.add(entrypoint.trim());
    }
    return Array.from(options);
  };

  // Step 2 functions
  const addRequiredFile = () => {
    const path = newRequiredFile.trim();
    if (path && !requiredFiles.includes(path)) {
      setRequiredFiles([...requiredFiles, path]);
      setNewRequiredFile("");
      if (!entrypoint) setEntrypoint(path);
    }
  };

  const removeRequiredFile = (file: string) => {
    setRequiredFiles(requiredFiles.filter((f) => f !== file));
    if (entrypoint === file) setEntrypoint("");
  };

  const addFileRequirement = () => {
    const nextId = fileRequirements.length + 1;
    const newReq: FileRequirementConfig = {
      label: `Required File Rule ${nextId}`,
      paths: [""],
    };
    setFileRequirements([...fileRequirements, newReq]);
  };

  const removeFileRequirement = (idx: number) => {
    setFileRequirements(fileRequirements.filter((_, i) => i !== idx));
  };

  const updateFileRequirement = <K extends keyof FileRequirementConfig>(
    idx: number,
    field: K,
    val: FileRequirementConfig[K],
  ) => {
    setFileRequirements((prev) =>
      prev.map((req, i) => (i === idx ? { ...req, [field]: val } : req)),
    );
  };

  const updateFileRequirementPath = (
    reqIdx: number,
    pathIdx: number,
    val: string,
  ) => {
    setFileRequirements((prev) =>
      prev.map((req, i) => {
        if (i === reqIdx) {
          const currentPaths = req.paths || [""];
          const newPaths = [...currentPaths];
          newPaths[pathIdx] = val;
          return { ...req, paths: newPaths };
        }
        return req;
      }),
    );
  };

  const addFileRequirementPath = (reqIdx: number) => {
    setFileRequirements((prev) =>
      prev.map((req, i) => {
        if (i === reqIdx) {
          const currentPaths = req.paths || [""];
          return { ...req, paths: [...currentPaths, ""] };
        }
        return req;
      }),
    );
  };

  const removeFileRequirementPath = (reqIdx: number, pathIdx: number) => {
    setFileRequirements((prev) =>
      prev.map((req, i) => {
        if (i === reqIdx) {
          const currentPaths = req.paths || [""];
          const newPaths = currentPaths.filter((_, pIdx) => pIdx !== pathIdx);
          return { ...req, paths: newPaths };
        }
        return req;
      }),
    );
  };

  const toggleFileRequirementGlob = (reqIdx: number, isGlob: boolean) => {
    setFileRequirements((prev) =>
      prev.map((req, i) => {
        if (i === reqIdx) {
          if (isGlob) {
            return { label: req.label, pattern: "*.py" };
          } else {
            const firstPath = req.paths?.[0] || "";
            return { label: req.label, paths: [firstPath] };
          }
        }
        return req;
      }),
    );
  };

  // Step 3 functions
  const addRubricGroup = () => {
    const nextId = rubricGroups.length + 1;
    const newGroup: RubricGroupConfig = {
      key: `group_${nextId}`,
      label: `Group ${nextId}`,
    };
    setRubricGroups([...rubricGroups, newGroup]);
  };

  const removeRubricGroup = (key: string) => {
    setRubricGroups(rubricGroups.filter((g) => g.key !== key));
    // Clear rubric_group_key references on items
    setTests(
      tests.map((t) =>
        t.rubric_group_key === key ? { ...t, rubric_group_key: null } : t,
      ),
    );
    setManualRubricItems(
      manualRubricItems.map((m) =>
        m.rubric_group_key === key ? { ...m, rubric_group_key: null } : m,
      ),
    );
  };

  const updateRubricGroup = (
    key: string,
    field: "key" | "label",
    val: string,
  ) => {
    const sanitizedVal = field === "key" ? sanitizeKey(val) : val;
    setRubricGroups((prev) =>
      prev.map((g) => (g.key === key ? { ...g, [field]: sanitizedVal } : g)),
    );
    if (field === "key") {
      // Cascade key update to items referencing this group
      setTests(
        tests.map((t) =>
          t.rubric_group_key === key
            ? { ...t, rubric_group_key: sanitizedVal }
            : t,
        ),
      );
      setManualRubricItems(
        manualRubricItems.map((m) =>
          m.rubric_group_key === key
            ? { ...m, rubric_group_key: sanitizedVal }
            : m,
        ),
      );
    }
  };

  // Reusable list item update helper with auto-derivation
  const updateListItemField = <
    T extends { key: string; label: string; points?: number },
  >(
    setter: React.Dispatch<React.SetStateAction<T[]>>,
    key: string,
    field: keyof T,
    val: unknown,
    customKeyMap: Record<string, boolean>,
    setCustomKeyMap: React.Dispatch<
      React.SetStateAction<Record<string, boolean>>
    >,
  ) => {
    setter((prev) =>
      prev.map((item) => {
        if (item.key === key) {
          const updated: T = { ...item, [field]: val };
          if (field === "label") {
            if (!customKeyMap[key]) {
              const derived = slugifyKey(String(val));
              if (derived) {
                updated.key = derived;
              }
            }
          }
          if (field === "key") {
            const sanitized = sanitizeKey(String(val));
            updated.key = sanitized;
            setCustomKeyMap((c) => ({ ...c, [sanitized]: true, [key]: true }));
          }
          if (field === "points") {
            updated.points = Math.max(0, parseInt(String(val)) || 0);
          }
          return updated;
        }
        return item;
      }),
    );
  };

  const addTest = () => {
    const nextId = tests.length + 1;
    setTests([
      ...tests,
      {
        key: `test_item_${nextId}`,
        label: `Test Item ${nextId}`,
        points: 5,
        extra_credit: false,
        rubric_group_key: null,
      },
    ]);
  };

  const removeTest = (key: string) => {
    setTests(tests.filter((t) => t.key !== key));
  };

  const updateTestField = (
    key: string,
    field: keyof ScoringItemConfig,
    val: unknown,
  ) => {
    updateListItemField(
      setTests,
      key,
      field,
      val,
      customTestKeys,
      setCustomTestKeys,
    );
  };

  const renderTestDetails = (test: ScoringItemConfig) => {
    const inputs = test.inputs || [];
    const outputs = test.outputs || [];

    const handleAddCase = () => {
      const nextInputs = [...inputs, ""];
      const nextOutputs = [...outputs, ""];
      updateTestField(test.key, "inputs", nextInputs);
      updateTestField(test.key, "outputs", nextOutputs);
    };

    const handleUpdateCase = (
      index: number,
      field: "input" | "output",
      value: string,
    ) => {
      if (field === "input") {
        const nextInputs = [...inputs];
        nextInputs[index] = value;
        updateTestField(test.key, "inputs", nextInputs);
      } else {
        const nextOutputs = [...outputs];
        nextOutputs[index] = value;
        updateTestField(test.key, "outputs", nextOutputs);
      }
    };

    const handleRemoveCase = (index: number) => {
      const nextInputs = inputs.filter((_, idx) => idx !== index);
      const nextOutputs = outputs.filter((_, idx) => idx !== index);
      const finalInputs = nextInputs.length > 0 ? nextInputs : null;
      const finalOutputs = nextOutputs.length > 0 ? nextOutputs : null;
      updateTestField(test.key, "inputs", finalInputs);
      updateTestField(test.key, "outputs", finalOutputs);
    };

    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-4 max-h-[300px] overflow-y-auto">
        <div className="flex justify-between items-center">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide">
            Compare Output Test Cases for:{" "}
            <span className="font-mono text-indigo-600">{test.key}</span>
          </h4>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddCase}
            className="text-xs h-7"
          >
            <PlusIcon className="size-3 mr-1" /> Add Case Scenario
          </Button>
        </div>

        {inputs.length === 0 ? (
          <p className="text-xs text-slate-400 italic">
            No input/output test cases configured. This item behaves as a
            standard unit test.
          </p>
        ) : (
          <div className="space-y-4">
            {inputs.map((inp, index) => (
              <div
                key={index}
                className="bg-white p-3 rounded border border-slate-200 shadow-2xs relative"
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold text-slate-500">
                    Case #{index + 1}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemoveCase(index)}
                    className="text-slate-400 hover:text-red-500 transition-colors p-1 cursor-pointer"
                  >
                    <XIcon className="size-3.5" />
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">
                      Input (stdin)
                    </label>
                    <textarea
                      value={inp}
                      onChange={(e) =>
                        handleUpdateCase(index, "input", e.target.value)
                      }
                      placeholder="Sequence of inputs (e.g. 2\n3)"
                      rows={2}
                      className="w-full min-h-[60px] max-h-40 rounded border border-slate-300 bg-white p-2 text-xs font-mono focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-500 uppercase">
                      Expected Output
                    </label>
                    <textarea
                      value={outputs[index] || ""}
                      onChange={(e) =>
                        handleUpdateCase(index, "output", e.target.value)
                      }
                      placeholder="Expected program output"
                      rows={2}
                      className="w-full min-h-[60px] max-h-40 rounded border border-slate-300 bg-white p-2 text-xs font-mono focus:border-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const addManualItem = () => {
    const nextId = manualRubricItems.length + 1;
    setManualRubricItems([
      ...manualRubricItems,
      {
        key: `manual_item_${nextId}`,
        label: `Manual Item ${nextId}`,
        points: 5,
        extra_credit: false,
        rubric_group_key: null,
      },
    ]);
  };

  const removeManualItem = (key: string) => {
    setManualRubricItems(manualRubricItems.filter((m) => m.key !== key));
  };

  const updateManualItemField = (
    key: string,
    field: keyof ManualRubricItemConfig,
    val: unknown,
  ) => {
    updateListItemField(
      setManualRubricItems,
      key,
      field,
      val,
      customManualKeys,
      setCustomManualKeys,
    );
  };

  // Step 4 functions
  const handleConceptChange = (concept: string) => {
    setConcepts((prev) =>
      prev.includes(concept)
        ? prev.filter((c) => c !== concept)
        : [...prev, concept],
    );
  };

  // Step 5 functions
  const addDependency = () => {
    const dep = newDependency.trim();
    if (dep && !dependencies.includes(dep) && isValidDependency(dep)) {
      setDependencies([...dependencies, dep]);
      setNewDependency("");
    }
  };

  const removeDependency = (dep: string) => {
    setDependencies(dependencies.filter((d) => d !== dep));
  };

  const handleDeleteAssignment = async () => {
    if (
      !confirm(
        `Are you sure you want to delete assignment "${assignmentId}"? This action will deactivate the assignment.`,
      )
    ) {
      return;
    }
    try {
      await deleteStaffAssignment(courseId, assignmentId);
      router.push(`/staff/courses/${courseId}/assignments`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete assignment.",
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">
          Loading assignment details...
        </p>
      </div>
    );
  }

  const allPossibleConcepts = Object.values(conceptMeta).map((item) => ({
    key: item.key,
    title: item.title,
    patterns: item.syntax_patterns,
  }));

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-10">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <div className="space-y-1">
            <BackLink
              href={`/staff/courses/${courseId}/assignments`}
              variant="compact"
            >
              Back to course details
            </BackLink>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              Grading Setup
            </h1>
            <p className="text-slate-500">
              Configure parameters for assignment &quot;{assignmentId}&quot;
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={handleCopyStudentLink}
              className="flex items-center gap-1.5 cursor-pointer"
            >
              {copied ? (
                <>
                  <CheckIcon className="size-4 text-green-600" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <CopyIcon className="size-4" />
                  <span>Copy Student Link</span>
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={handleDeleteAssignment}
              className="flex items-center gap-1.5 text-red-600 border-red-200 hover:bg-red-50 hover:text-red-700 cursor-pointer"
            >
              <Trash2Icon className="size-4" />
              <span>Delete Assignment</span>
            </Button>
            <Button variant="outline" asChild>
              <Link
                href={`/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`}
              >
                Manage Artifacts
              </Link>
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              <SaveIcon className="mr-2 size-4" /> Save Setup
            </Button>
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 whitespace-pre-line">
            <div className="flex gap-2 items-start font-semibold mb-1">
              <ShieldAlertIcon className="size-4 shrink-0 mt-0.5" />
              <span>Validation Warnings</span>
            </div>
            {error}
          </div>
        )}
        {successMsg && (
          <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-600 flex items-center gap-2">
            <CheckCircle2Icon className="size-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        <Tabs defaultValue="metadata" className="w-full">
          <TabsList className="grid w-full grid-cols-6 mb-6">
            <TabsTrigger value="metadata">Step 1: Info</TabsTrigger>
            <TabsTrigger value="bundle">Step 2: File Requirements</TabsTrigger>
            <TabsTrigger value="rubrics">Step 3: Rubric</TabsTrigger>
            <TabsTrigger value="whitelist">Step 4: Concepts</TabsTrigger>
            <TabsTrigger value="dependencies">Step 5: Libraries</TabsTrigger>
            <TabsTrigger value="validation">Preflight</TabsTrigger>
          </TabsList>

          {/* STEP 1: BASIC METADATA */}
          <TabsContent value="metadata">
            <Card>
              <CardHeader>
                <CardTitle>Basic Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">
                      Assignment Title *
                    </label>
                    <Input
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g. Project 1: Calculator"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">
                      Module Assignment
                    </label>
                    <Select
                      value={moduleId !== null ? String(moduleId) : "none"}
                      onValueChange={(val) =>
                        setModuleId(val === "none" ? null : parseInt(val, 10))
                      }
                    >
                      <SelectTrigger className="w-full">
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
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">
                      Programming Language (Read-only)
                    </label>
                    <Input
                      value={setup?.language}
                      disabled
                      className="bg-slate-100 font-mono text-slate-500"
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2 pt-4 border-t border-slate-100">
                  <input
                    type="checkbox"
                    id="sandbox"
                    checked={sandboxEnabled}
                    onChange={(e) => setSandboxEnabled(e.target.checked)}
                    className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label
                    htmlFor="sandbox"
                    className="text-sm font-semibold text-slate-700 cursor-pointer"
                  >
                    Enable Student Sandbox Access
                  </label>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* STEP 2: FILE REQUIREMENTS */}
          <TabsContent value="bundle">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div>
                  <CardTitle>File Requirements</CardTitle>
                  <CardDescription className="mt-1">
                    Set up required files and select which file serves as the
                    primary execution entrypoint.
                  </CardDescription>
                </div>
                <Button
                  type="button"
                  onClick={addFileRequirement}
                  variant="outline"
                  size="sm"
                >
                  <PlusCircleIcon className="size-4 mr-1.5" /> Add Required File
                </Button>
              </CardHeader>
              <CardContent className="space-y-6 pt-4">
                <div className="space-y-4">
                  {fileRequirements.map((req, idx) => {
                    const isEntrypoint = Boolean(req.paths?.includes(entrypoint));
                    return (
                      <div
                        key={idx}
                        className={`relative rounded-lg border p-4 shadow-xs space-y-4 transition-colors ${
                          isEntrypoint
                            ? "border-indigo-300 bg-indigo-50/30"
                            : "border-slate-200 bg-white"
                        }`}
                      >
                        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                          <label className="flex items-center gap-2 cursor-pointer font-semibold text-xs text-slate-700">
                            <input
                              type="radio"
                              name="entrypoint_selection"
                              checked={isEntrypoint}
                              onChange={() => {
                                if (req.paths?.[0]) {
                                  setEntrypoint(req.paths[0]);
                                }
                              }}
                              className="size-4 text-indigo-600 focus:ring-indigo-500"
                            />
                            <span>Primary Entrypoint</span>
                          </label>
                          <button
                            type="button"
                            onClick={() => removeFileRequirement(idx)}
                            className="text-slate-400 hover:text-red-500 transition-colors cursor-pointer"
                          >
                            <Trash2Icon className="size-4" />
                          </button>
                        </div>

                        <div className="space-y-1">
                          <label className="text-xs font-semibold text-slate-500 uppercase">
                            Label / Rule Name *
                          </label>
                          <Input
                            value={req.label || ""}
                            onChange={(e) =>
                              updateFileRequirement(
                                idx,
                                "label",
                                e.target.value,
                              )
                            }
                            placeholder="e.g. Main Entrypoint Script"
                            className="text-xs"
                          />
                        </div>

                        {/* Paths / Pattern management */}
                        <div className="space-y-2 pt-2 border-t border-slate-100">
                          <div className="flex items-center justify-between">
                            <label className="text-xs font-semibold text-slate-500 uppercase">
                              {req.pattern !== undefined && req.pattern !== null
                                ? "Glob Pattern"
                                : "Allowed File Name(s)"}
                            </label>
                            <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer select-none">
                              <input
                                type="checkbox"
                                checked={
                                  req.pattern !== undefined &&
                                  req.pattern !== null
                                }
                                onChange={(e) =>
                                  toggleFileRequirementGlob(
                                    idx,
                                    e.target.checked,
                                  )
                                }
                                className="size-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                              />
                              <span>Treat as glob pattern (e.g. *.py, lab?.txt)</span>
                            </label>
                          </div>

                          {req.pattern !== undefined && req.pattern !== null ? (
                            <div className="space-y-1">
                              <Input
                                value={req.pattern}
                                onChange={(e) =>
                                  updateFileRequirement(
                                    idx,
                                    "pattern",
                                    e.target.value,
                                  )
                                }
                                placeholder="e.g. *.py"
                                className="font-mono text-xs max-w-md"
                              />
                              <p className="text-[11px] text-slate-400">
                                Evaluated using Python&apos;s <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-600">Path.glob()</code> syntax (use <code className="font-mono bg-slate-100 px-1 py-0.5 rounded text-slate-600">**/*.py</code> for recursive subfolders).
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-2">
                              {(req.paths || [""]).map((path, pathIdx) => (
                                <div
                                  key={pathIdx}
                                  className="flex gap-2 items-center"
                                >
                                  <Input
                                    value={path}
                                    onChange={(e) => {
                                      updateFileRequirementPath(
                                        idx,
                                        pathIdx,
                                        e.target.value,
                                      );
                                      if (isEntrypoint && pathIdx === 0) {
                                        setEntrypoint(e.target.value);
                                      }
                                    }}
                                    placeholder={
                                      pathIdx === 0
                                        ? "e.g. main.py"
                                        : "e.g. solution.py"
                                    }
                                    className="font-mono text-xs max-w-md"
                                  />
                                  {(req.paths?.length || 0) > 1 && (
                                    <Button
                                      type="button"
                                      variant="ghost"
                                      size="sm"
                                      onClick={() =>
                                        removeFileRequirementPath(idx, pathIdx)
                                      }
                                    >
                                      <XIcon className="size-3.5 text-slate-400 hover:text-red-500" />
                                    </Button>
                                  )}
                                </div>
                              ))}

                              <div className="flex flex-wrap items-center gap-4 pt-1">
                                <Button
                                  type="button"
                                  onClick={() => addFileRequirementPath(idx)}
                                  variant="outline"
                                  size="sm"
                                  className="h-7 text-xs text-indigo-600 border-indigo-200 hover:bg-indigo-50"
                                >
                                  <PlusIcon className="size-3 mr-1" /> Add
                                  Alternate File Name
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  {fileRequirements.length === 0 && (
                    <div className="rounded-lg border border-dashed border-slate-200 p-8 text-center">
                      <p className="text-sm font-medium text-slate-600">
                        No file requirements configured.
                      </p>
                      <p className="text-xs text-slate-400 mt-1 mb-4">
                        Add at least one required file to configure execution.
                      </p>
                      <Button
                        type="button"
                        onClick={addFileRequirement}
                        variant="outline"
                        size="sm"
                      >
                        <PlusCircleIcon className="size-4 mr-1.5" /> Add
                        Required File
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* STEP 3: RAW SCORING RUBRICS */}
          <TabsContent value="rubrics">
            <Card>
              <CardHeader>
                <CardTitle>Raw Scoring Rubrics</CardTitle>
                <CardDescription>
                  Configure autograded tests, manual rubric checks, and their
                  visual groups.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Rubric Groups Management */}
                <div className="space-y-3 bg-slate-50 p-4 rounded-lg border border-slate-100">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">
                        Rubric Group Headers
                      </h3>
                      <p className="text-xs text-slate-500">
                        Visual headings used in grading tables to group scoring
                        items.
                      </p>
                    </div>
                    <Button
                      type="button"
                      onClick={addRubricGroup}
                      variant="outline"
                      size="sm"
                    >
                      <PlusIcon className="size-4 mr-1" /> Add Group
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {rubricGroups.map((group) => (
                      <div
                        key={group.key}
                        className="flex gap-2 items-center bg-white p-2.5 rounded border border-slate-200 shadow-xs relative group-item"
                      >
                        <div className="grid grid-cols-2 gap-2 grow">
                          <Input
                            value={group.key}
                            onChange={(e) =>
                              updateRubricGroup(
                                group.key,
                                "key",
                                e.target.value,
                              )
                            }
                            placeholder="Slug Key"
                            className="text-xs font-mono"
                          />
                          <Input
                            value={group.label}
                            onChange={(e) =>
                              updateRubricGroup(
                                group.key,
                                "label",
                                e.target.value,
                              )
                            }
                            placeholder="Display Label"
                            className="text-xs font-semibold"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => removeRubricGroup(group.key)}
                          className="text-slate-400 hover:text-red-500 transition-colors p-1 cursor-pointer"
                        >
                          <XIcon className="size-4" />
                        </button>
                      </div>
                    ))}
                    {rubricGroups.length === 0 && (
                      <p className="text-xs text-slate-400 italic col-span-2">
                        No rubric groups created. Scoring items will be
                        ungrouped.
                      </p>
                    )}
                  </div>
                </div>

                {/* Autograded tests section */}
                <div className="space-y-2">
                  {setup?.artifacts.find(
                    (art) => art.artifact_type === "pytest_file",
                  ) && (
                    <div className="flex justify-end">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const art = setup?.artifacts.find(
                            (art) => art.artifact_type === "pytest_file",
                          );
                          if (art) {
                            openCodeEditor(
                              art.artifact_key,
                              "pytest_file",
                              art.display_filename || "test_suite.py",
                            );
                          }
                        }}
                      >
                        <FileTextIcon className="size-4 mr-1.5" /> Edit Test
                        Code
                      </Button>
                    </div>
                  )}
                  <ScoringItemsTable
                    items={tests}
                    onUpdate={updateTestField}
                    onDelete={removeTest}
                    rubricGroups={rubricGroups}
                    title="Autograded Test Criteria"
                    description="Evaluations backed by pytest tests. The Key maps directly to a pytest marker suffix (e.g. key `calc` targets `@pytest.mark.ag_calc`)."
                    addButtonLabel="Add Test"
                    onAdd={addTest}
                    emptyText="No autograded tests configured. At least one pytest marker test is required."
                    renderDetails={renderTestDetails}
                  />
                </div>

                {/* Manual Rubric Items section */}
                <div className="pt-6 border-t border-slate-100">
                  <ScoringItemsTable
                    items={manualRubricItems}
                    onUpdate={updateManualItemField}
                    onDelete={removeManualItem}
                    rubricGroups={rubricGroups}
                    title="Manual Grading Criteria (Optional)"
                    description="Rubric criteria evaluated manually by staff after a run (e.g. style, code organization)."
                    addButtonLabel="Add Manual Item"
                    onAdd={addManualItem}
                    emptyText="No manual rubric items configured."
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* STEP 4: WHITELIST CONCEPTS & INPUT SCENARIOS */}
          <TabsContent value="whitelist">
            <Card>
              <CardHeader>
                <CardTitle>Concepts & Input Scenarios</CardTitle>
                <CardDescription>
                  Define what syntax structures are whitelisted and keyboard
                  scenarios for interactive CLI tests.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Inherited Course Module Concepts section */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">
                        Inherited Course Module Concepts
                      </h3>
                    </div>
                    <Link
                      href={`/staff/courses/${courseId}/settings`}
                      className="text-xs text-indigo-600 font-semibold hover:underline flex items-center gap-1"
                    >
                      Manage Course Modules &rarr;
                    </Link>
                  </div>

                  {moduleId !== null &&
                  setup?.effective_allowed_concepts &&
                  setup.effective_allowed_concepts.length > 0 ? (
                    <div className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-4 space-y-3">
                      <div className="text-xs text-indigo-900 font-medium">
                        Assigned Module ID{" "}
                        <span className="font-mono font-bold text-indigo-700">
                          #{moduleId}
                        </span>{" "}
                        — Inherited Syntax Concepts (
                        {setup.effective_allowed_concepts.length}):
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {setup.effective_allowed_concepts.map((key) => (
                          <span
                            key={key}
                            className="inline-flex items-center gap-1 rounded-md bg-indigo-100 px-2.5 py-1 text-xs font-semibold text-indigo-800 border border-indigo-200"
                          >
                            <CheckCircle2Icon className="size-3.5 text-indigo-600" />
                            {conceptMeta[key]?.title || key}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-2">
                      <div className="text-xs font-semibold text-slate-700">
                        {moduleId === null
                          ? "No Course Module Assigned"
                          : "No Concepts Configured for Module"}
                      </div>
                      <p className="text-xs text-slate-500">
                        Assign a Course Module in Step 1 (General Settings) to
                        automatically inherit concept syntax boundaries across
                        assignments.
                      </p>
                    </div>
                  )}
                </div>

              </CardContent>
            </Card>
          </TabsContent>

          {/* STEP 5: EXECUTION DEPENDENCIES */}
          <TabsContent value="dependencies">
            <Card>
              <CardHeader>
                <CardTitle>Execution Dependencies</CardTitle>
                <CardDescription>
                  List external Python package dependencies required by student
                  code.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-800">
                    Required Libraries
                  </h3>
                  <p className="text-xs text-slate-400">
                    Pip packages installed in sandbox containers prior to
                    execution (e.g. numpy, pillow).
                  </p>

                  <TagBadgeList
                    tags={dependencies}
                    onRemove={removeDependency}
                    emptyText="No external Python dependencies required."
                  />

                  <div className="flex gap-2 max-w-sm">
                    <Input
                      value={newDependency}
                      onChange={(e) => setNewDependency(e.target.value)}
                      placeholder="e.g. numpy"
                      className="font-mono text-sm"
                      onKeyDown={(e) => e.key === "Enter" && addDependency()}
                    />
                    <Button
                      type="button"
                      onClick={addDependency}
                      variant="outline"
                      size="sm"
                    >
                      <PlusIcon className="size-4 mr-1" /> Add Dependency
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* PREFLIGHT VALIDATION */}
          <TabsContent value="validation">
            <Card>
              <CardHeader>
                <CardTitle>Test Model Solution</CardTitle>
                <CardDescription>
                  Execute model solutions against the config suite. Ensure test
                  parity.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Button
                    onClick={triggerValidation}
                    disabled={
                      validation.status === "queue" ||
                      validation.status === "run"
                    }
                  >
                    <PlayIcon className="mr-2 size-4" /> Run Validation
                  </Button>
                </div>

                {validation.status !== "idle" && (
                  <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-900">
                        Validation Run Status
                      </h4>
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

                    {(validation.status === "queue" ||
                      validation.status === "run") && (
                      <p className="text-sm text-slate-500 animate-pulse">
                        Pipeline executing in Sandbox Kata container. Polling
                        results...
                      </p>
                    )}

                    {validation.status === "success" && (
                      <div className="space-y-2">
                        <div className="flex items-center text-green-700 gap-1.5 text-sm font-semibold">
                          <CheckCircle2Icon className="size-4" /> Parity
                          Confirmed. Model Solution scored {validation.score} /{" "}
                          {validation.max_score}.
                        </div>
                      </div>
                    )}

                    {validation.status === "failure" && (
                      <div className="space-y-2">
                        <div className="flex items-center text-red-700 gap-1.5 text-sm font-semibold">
                          <ShieldAlertIcon className="size-4" /> Pipeline
                          validation failures found:
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

        {/* Code Editor Modal Overlay */}
        {isCodeModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-fade-in">
            <div className="bg-white rounded-lg border border-slate-200 shadow-xl w-full max-w-5xl h-[85vh] flex flex-col">
              <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 rounded-t-lg">
                <div className="flex items-center gap-2">
                  <FileTextIcon className="size-5 text-indigo-600 animate-pulse" />
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">
                      Editing Grading Code: {editArtifactFilename}
                    </h3>
                    <p className="text-xs text-slate-400">
                      Directly modify the test suite content on the server.
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCodeModalOpen(false)}
                  className="text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                >
                  <XIcon className="size-5" />
                </button>
              </div>

              {codeEditorError && (
                <div className="bg-red-50 text-red-600 p-3 text-xs border-b border-red-100 flex items-center gap-2">
                  <ShieldAlertIcon className="size-4 shrink-0" />
                  <span>{codeEditorError}</span>
                </div>
              )}

              <div className="grow bg-slate-900 overflow-hidden relative flex items-center justify-center">
                {isLoadingCode ? (
                  <p className="text-xs text-slate-400 animate-pulse font-mono">
                    Fetching file content from server...
                  </p>
                ) : (
                  <MonacoEditor
                    height="100%"
                    width="100%"
                    defaultLanguage="python"
                    defaultValue={editCodeText}
                    onChange={(val) => setEditCodeText(val || "")}
                  />
                )}
              </div>

              <div className="p-4 border-t border-slate-200 flex justify-end gap-2 bg-slate-50 rounded-b-lg">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCodeModalOpen(false)}
                  disabled={isSavingCode}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={saveCodeChanges}
                  disabled={isSavingCode}
                >
                  <SaveIcon className="size-4 mr-1.5" />
                  {isSavingCode ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
