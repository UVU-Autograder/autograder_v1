"use client";

import { use, useState, useEffect } from "react";
import Link from "next/link";
import {
  ArrowLeftIcon,
  SaveIcon,
  ShieldAlertIcon,
  CheckCircle2Icon,
  PlayIcon,
  PlusIcon,
  Trash2Icon,
  XIcon,
  HelpCircleIcon,
  PlusCircleIcon,
  FileTextIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api-client";
import MonacoEditor from "@/components/monaco-editor";

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

type TestItemConfig = {
  key: string;
  label: string;
  points: number;
  extra_credit: boolean;
  rubric_group_key?: string | null;
};

type ManualRubricItemConfig = {
  key: string;
  label: string;
  points: number;
  extra_credit: boolean;
  rubric_group_key?: string | null;
};

type StdinScenarioConfig = {
  key: string;
  label: string;
  stdin: string[];
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
  tests: TestItemConfig[];
  rubric_groups?: RubricGroupConfig[];
  completion_requirements?: CompletionRequirementConfig[];
  manual_rubric_items?: ManualRubricItemConfig[];
  execution?: {
    dependencies?: string[];
  };
  stdin_scenarios?: StdinScenarioConfig[];
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
        <span key={tag} className="inline-flex items-center gap-1 bg-slate-100 text-slate-800 text-xs font-mono px-2 py-1 rounded border border-slate-200">
          {tag}
          <button type="button" onClick={() => onRemove(tag)} className="text-slate-400 hover:text-red-500 transition-colors cursor-pointer">
            <XIcon className="size-3" />
          </button>
        </span>
      ))}
      {tags.length === 0 && (
        <span className="text-xs text-slate-400 italic">
          {emptyText}
        </span>
      )}
    </div>
  );
}

// Reusable Scoring Items Table component
type ScoringItemsTableProps<T extends { key: string; label: string; points: number; extra_credit: boolean; rubric_group_key?: string | null }> = {
  items: T[];
  onUpdate: (key: string, field: keyof T, val: any) => void;
  onDelete: (key: string) => void;
  rubricGroups: RubricGroupConfig[];
  title: string;
  description: string;
  addButtonLabel: string;
  onAdd: () => void;
  emptyText: string;
};

function ScoringItemsTable<T extends { key: string; label: string; points: number; extra_credit: boolean; rubric_group_key?: string | null }>({
  items,
  onUpdate,
  onDelete,
  rubricGroups,
  title,
  description,
  addButtonLabel,
  onAdd,
  emptyText
}: ScoringItemsTableProps<T>) {
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
              <th className="py-2 pr-2">Key *</th>
              <th className="py-2 px-2">Student-Facing Description</th>
              <th className="py-2 px-2 w-20">Points</th>
              <th className="py-2 px-2 w-24 text-center">Extra Credit?</th>
              <th className="py-2 px-2">Rubric Group</th>
              <th className="py-2 pl-2 text-right">Delete</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((item) => (
              <tr key={item.key} className="hover:bg-slate-50/50">
                <td className="py-2 pr-2">
                  <Input
                    value={item.key}
                    onChange={(e) => onUpdate(item.key, "key" as keyof T, e.target.value)}
                    className="font-mono text-xs h-8"
                  />
                </td>
                <td className="py-2 px-2">
                  <Input
                    value={item.label}
                    onChange={(e) => onUpdate(item.key, "label" as keyof T, e.target.value)}
                    className="text-xs h-8"
                  />
                </td>
                <td className="py-2 px-2">
                  <Input
                    type="number"
                    value={item.points}
                    onChange={(e) => onUpdate(item.key, "points" as keyof T, e.target.value)}
                    className="w-16 h-8 text-xs text-center"
                  />
                </td>
                <td className="py-2 px-2 text-center">
                  <input
                    type="checkbox"
                    checked={item.extra_credit}
                    onChange={(e) => onUpdate(item.key, "extra_credit" as keyof T, e.target.checked)}
                    className="size-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                  />
                </td>
                <td className="py-2 px-2">
                  <select
                    value={item.rubric_group_key || ""}
                    onChange={(e) => onUpdate(item.key, "rubric_group_key" as keyof T, e.target.value || null)}
                    className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs focus:border-indigo-500 focus:outline-none h-8"
                  >
                    <option value="">-- None --</option>
                    {rubricGroups.map((g) => (
                      <option key={g.key} value={g.key}>{g.label || g.key}</option>
                    ))}
                  </select>
                </td>
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
            ))}
          </tbody>
        </table>
        {items.length === 0 && (
          <p className="text-xs text-slate-400 italic text-center py-4">{emptyText}</p>
        )}
      </div>
    </div>
  );
}

export default function SetupWizardPage({ params }: PageProps) {
  const { courseId, assignmentId } = use(params);
  const [setup, setSetup] = useState<StaffAssignmentSetup | null>(null);
  
  // Step 1
  const [title, setTitle] = useState("");
  const [sandboxEnabled, setSandboxEnabled] = useState(true);

  // Step 2
  const [requiredFiles, setRequiredFiles] = useState<string[]>([]);
  const [entrypoint, setEntrypoint] = useState("");
  const [newRequiredFile, setNewRequiredFile] = useState("");
  const [fileRequirements, setFileRequirements] = useState<FileRequirementConfig[]>([]);

  // Step 3
  const [tests, setTests] = useState<TestItemConfig[]>([]);
  const [manualRubricItems, setManualRubricItems] = useState<ManualRubricItemConfig[]>([]);
  const [rubricGroups, setRubricGroups] = useState<RubricGroupConfig[]>([]);

  // Step 4
  const [concepts, setConcepts] = useState<string[]>([]);
  const [customConcepts, setCustomConcepts] = useState<string[]>([]);
  const [newCustomConcept, setNewCustomConcept] = useState("");
  const [stdinScenarios, setStdinScenarios] = useState<StdinScenarioConfig[]>([]);

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

  // Centralized State Initialization Helper
  const syncSetupState = (data: StaffAssignmentSetup) => {
    const config = data.config_json;
    setSetup(data);
    setTitle(data.title);
    setSandboxEnabled(data.sandbox_enabled);

    // Step 2
    setRequiredFiles(config.bundle?.required_files || []);
    setEntrypoint(config.bundle?.entrypoint || "");
    setFileRequirements(config.bundle?.file_requirements || []);

    // Step 3
    setTests(config.tests || []);
    setManualRubricItems(config.manual_rubric_items || []);
    setRubricGroups(config.rubric_groups || []);

    // Step 4
    const additions = config.concepts?.additions || [];
    const predefined = ["variables", "conditionals", "loops", "functions", "file-io", "image-processing"];
    setConcepts(additions.filter(c => predefined.includes(c)));
    setCustomConcepts(additions.filter(c => !predefined.includes(c)));
    setStdinScenarios(config.stdin_scenarios || []);

    // Step 5
    setDependencies(config.execution?.dependencies || []);
  };

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
        syncSetupState(data);
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

    const allTestKeys = tests.map(t => t.key);
    const allManualKeys = manualRubricItems.map(m => m.key);
    const allGroupKeys = rubricGroups.map(g => g.key);
    const allReqKeys = fileRequirements.map(f => f.key);
    const allScenarioKeys = stdinScenarios.map(s => s.key);

    // Generic list key validation
    const validateKeyList = (keys: string[], listName: string) => {
      keys.forEach(k => {
        if (!k.trim()) errors.push(`${listName} key cannot be empty.`);
        else if (!isValidKey(k)) {
          errors.push(`${listName} key "${k}" is invalid. Must start with a lowercase letter and contain only lowercase letters, numbers, and underscores.`);
        }
      });
    };

    validateKeyList(allTestKeys, "Test");
    validateKeyList(allManualKeys, "Manual Rubric Item");
    validateKeyList(allGroupKeys, "Rubric Group");
    validateKeyList(allReqKeys, "File Requirement");
    validateKeyList(allScenarioKeys, "Stdin Scenario");

    // Duplicates
    const checkDuplicates = (keys: string[], name: string) => {
      const duplicates = keys.filter((k, idx) => keys.indexOf(k) !== idx);
      if (duplicates.length > 0) {
        errors.push(`Duplicate keys found in ${name}: ${Array.from(new Set(duplicates)).join(", ")}`);
      }
    };

    checkDuplicates(allTestKeys, "Tests");
    checkDuplicates(allManualKeys, "Manual Rubric Items");
    checkDuplicates(allGroupKeys, "Rubric Groups");
    checkDuplicates(allReqKeys, "File Requirements");
    checkDuplicates(allScenarioKeys, "Stdin Scenarios");

    // Tests & Manual overlap
    const overlap = allTestKeys.filter(k => allManualKeys.includes(k));
    if (overlap.length > 0) {
      errors.push(`Scoring item keys overlap between Tests and Manual Rubric Items: ${overlap.join(", ")}`);
    }

    // File Requirements paths counts
    fileRequirements.forEach(req => {
      if (req.requirement_type === "one_of") {
        if (req.paths.length < 2) {
          errors.push(`File requirement "${req.key}" (one_of) must have at least two paths.`);
        }
      } else {
        if (req.paths.length !== 1 || !req.paths[0].trim()) {
          errors.push(`File requirement "${req.key}" (${req.requirement_type}) must have exactly one path.`);
        }
      }
    });

    // Entrypoint verification
    const knownPaths = new Set(requiredFiles);
    fileRequirements.forEach(req => {
      if (req.requirement_type !== "pattern") {
        req.paths.forEach(p => {
          if (p.trim()) knownPaths.add(p.trim());
        });
      }
    });

    if (entrypoint && !knownPaths.has(entrypoint)) {
      errors.push(`Entrypoint "${entrypoint}" is not present in required_files or file requirement paths.`);
    }

    // Dependencies
    dependencies.forEach(dep => {
      if (!isValidDependency(dep)) {
        errors.push(`Dependency "${dep}" contains invalid characters. Allowed: alphanumeric, underscores, hyphens, and periods.`);
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
      setError(`Please resolve the following errors before saving:\n${clientErrors.join("\n")}`);
      setIsSaving(false);
      return;
    }

    // Map item keys to rubric groups dynamically on save
    const updatedRubricGroups = rubricGroups.map((group) => {
      const matchingItemKeys = [
        ...tests.filter((t) => t.rubric_group_key === group.key).map((t) => t.key),
        ...manualRubricItems.filter((m) => m.rubric_group_key === group.key).map((m) => m.key),
      ];
      return {
        ...group,
        item_keys: matchingItemKeys,
      };
    });

    // Sync renamed test keys in completion requirements
    const keyMap: Record<string, string> = {};
    if (setup.config_json.tests) {
      setup.config_json.tests.forEach((origTest, idx) => {
        const currentTest = tests[idx];
        if (currentTest && origTest.key !== currentTest.key) {
          keyMap[origTest.key] = currentTest.key;
        }
      });
    }

    const updatedCompletionRequirements = (setup.config_json.completion_requirements || []).map((req) => {
      const updatedTestKeys = req.test_keys.map((tk) => keyMap[tk] || tk);
      return {
        ...req,
        test_keys: updatedTestKeys,
      };
    });

    // Reconstruct the config_json reflecting updates
    const updatedConfig: AssignmentConfigV1 = {
      ...setup.config_json,
      schema_version: setup.config_json.schema_version || 1,
      bundle: {
        required_files: requiredFiles,
        entrypoint: entrypoint,
        file_requirements: fileRequirements,
      },
      concepts: {
        additions: [...concepts, ...customConcepts],
      },
      tests: tests.map(t => ({
        key: t.key,
        label: t.label,
        points: Number(t.points),
        extra_credit: t.extra_credit,
        rubric_group_key: t.rubric_group_key || null
      })),
      manual_rubric_items: manualRubricItems.map(m => ({
        key: m.key,
        label: m.label,
        points: Number(m.points),
        extra_credit: m.extra_credit,
        rubric_group_key: m.rubric_group_key || null
      })),
      rubric_groups: updatedRubricGroups,
      completion_requirements: updatedCompletionRequirements,
      stdin_scenarios: stdinScenarios,
      execution: {
        dependencies: dependencies,
      }
    };

    try {
      const data = await apiClient.put<StaffAssignmentSetup>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/setup`,
        {
          title,
          sandbox_enabled: sandboxEnabled,
          config_json: updatedConfig,
        }
      );
      syncSetupState(data);
      setSuccessMsg("Configuration saved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update configuration.");
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

  const fetchArtifactText = async (key: string): Promise<string> => {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
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

  const openCodeEditor = async (key: string, type: string, filename: string) => {
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
      setCodeEditorError(err instanceof Error ? err.message : "Failed to load artifact code.");
      setIsLoadingCode(false);
    }
  };

  const saveCodeChanges = async () => {
    if (!editArtifactKey) return;
    setIsSavingCode(true);
    setCodeEditorError(null);

    const file = new File([editCodeText], editArtifactFilename, { type: "text/plain" });
    const formData = new FormData();
    formData.append("file", file);
    formData.append("artifact_key", editArtifactKey);
    formData.append("artifact_type", editArtifactType);

    try {
      await apiClient.postForm(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
        formData
      );
      setIsCodeModalOpen(false);
      setSuccessMsg(`Code saved successfully for '${editArtifactFilename}'.`);
      apiClient.get<StaffAssignmentSetup>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/setup`
      ).then((data) => {
        setSetup(data);
      }).catch(() => {});
    } catch (err) {
      setCodeEditorError(err instanceof Error ? err.message : "Failed to save code changes.");
    } finally {
      setIsSavingCode(false);
    }
  };

  // Helper selectors for entrypoint options
  const getEntrypointOptions = () => {
    const options = new Set(requiredFiles);
    fileRequirements.forEach(req => {
      if (req.requirement_type !== "pattern") {
        req.paths.forEach(p => {
          if (p.trim()) options.add(p.trim());
        });
      }
    });
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
    setRequiredFiles(requiredFiles.filter(f => f !== file));
    if (entrypoint === file) setEntrypoint("");
  };

  const addFileRequirement = () => {
    const nextId = fileRequirements.length + 1;
    const newReq: FileRequirementConfig = {
      key: `file_req_${nextId}`,
      label: `Required File Rule ${nextId}`,
      requirement_type: "exact",
      paths: [""]
    };
    setFileRequirements([...fileRequirements, newReq]);
  };

  const removeFileRequirement = (idx: number) => {
    setFileRequirements(fileRequirements.filter((_, i) => i !== idx));
  };

  const updateFileRequirement = (idx: number, field: keyof FileRequirementConfig, val: any) => {
    setFileRequirements(prev => prev.map((req, i) => {
      if (i === idx) {
        let updated = { ...req, [field]: val };
        // adjust paths size if requirement_type changes
        if (field === "requirement_type") {
          if (val === "one_of") {
            updated.paths = req.paths.length < 2 ? [...req.paths, ""] : req.paths;
          } else {
            updated.paths = [req.paths[0] || ""];
          }
        }
        if (field === "key") {
          updated.key = sanitizeKey(val);
        }
        return updated;
      }
      return req;
    }));
  };

  const updateFileRequirementPath = (reqIdx: number, pathIdx: number, val: string) => {
    setFileRequirements(prev => prev.map((req, i) => {
      if (i === reqIdx) {
        const newPaths = [...req.paths];
        newPaths[pathIdx] = val;
        return { ...req, paths: newPaths };
      }
      return req;
    }));
  };

  const addFileRequirementPath = (reqIdx: number) => {
    setFileRequirements(prev => prev.map((req, i) => {
      if (i === reqIdx) {
        return { ...req, paths: [...req.paths, ""] };
      }
      return req;
    }));
  };

  const removeFileRequirementPath = (reqIdx: number, pathIdx: number) => {
    setFileRequirements(prev => prev.map((req, i) => {
      if (i === reqIdx) {
        return { ...req, paths: req.paths.filter((_, pIdx) => pIdx !== pathIdx) };
      }
      return req;
    }));
  };

  // Step 3 functions
  const addRubricGroup = () => {
    const nextId = rubricGroups.length + 1;
    const newGroup: RubricGroupConfig = {
      key: `group_${nextId}`,
      label: `Group ${nextId}`,
      item_keys: []
    };
    setRubricGroups([...rubricGroups, newGroup]);
  };

  const removeRubricGroup = (key: string) => {
    setRubricGroups(rubricGroups.filter(g => g.key !== key));
    // Clear rubric_group_key references on items
    setTests(tests.map(t => t.rubric_group_key === key ? { ...t, rubric_group_key: null } : t));
    setManualRubricItems(manualRubricItems.map(m => m.rubric_group_key === key ? { ...m, rubric_group_key: null } : m));
  };

  const updateRubricGroup = (key: string, field: "key" | "label", val: string) => {
    const sanitizedVal = field === "key" ? sanitizeKey(val) : val;
    setRubricGroups(prev => prev.map(g => g.key === key ? { ...g, [field]: sanitizedVal } : g));
    if (field === "key") {
      // Cascade key update to items referencing this group
      setTests(tests.map(t => t.rubric_group_key === key ? { ...t, rubric_group_key: sanitizedVal } : t));
      setManualRubricItems(manualRubricItems.map(m => m.rubric_group_key === key ? { ...m, rubric_group_key: sanitizedVal } : m));
    }
  };

  // Reusable list item update helper
  const updateListItemField = <T extends { key: string }>(
    setter: React.Dispatch<React.SetStateAction<T[]>>,
    key: string,
    field: keyof T,
    val: any
  ) => {
    setter((prev) =>
      prev.map((item) => {
        if (item.key === key) {
          let finalVal = val;
          if (field === "key") finalVal = sanitizeKey(val);
          if (field === "points") finalVal = Math.max(0, parseInt(val) || 0);
          return { ...item, [field]: finalVal };
        }
        return item;
      })
    );
  };

  const addTest = () => {
    const nextId = tests.length + 1;
    setTests([...tests, {
      key: `test_item_${nextId}`,
      label: `Test Item ${nextId}`,
      points: 5,
      extra_credit: false,
      rubric_group_key: null
    }]);
  };

  const removeTest = (key: string) => {
    setTests(tests.filter(t => t.key !== key));
  };

  const updateTestField = (key: string, field: keyof TestItemConfig, val: any) => {
    updateListItemField(setTests, key, field, val);
  };

  const addManualItem = () => {
    const nextId = manualRubricItems.length + 1;
    setManualRubricItems([...manualRubricItems, {
      key: `manual_item_${nextId}`,
      label: `Manual Item ${nextId}`,
      points: 5,
      extra_credit: false,
      rubric_group_key: null
    }]);
  };

  const removeManualItem = (key: string) => {
    setManualRubricItems(manualRubricItems.filter(m => m.key !== key));
  };

  const updateManualItemField = (key: string, field: keyof ManualRubricItemConfig, val: any) => {
    updateListItemField(setManualRubricItems, key, field, val);
  };

  // Step 4 functions
  const handleConceptChange = (concept: string) => {
    setConcepts((prev) =>
      prev.includes(concept) ? prev.filter((c) => c !== concept) : [...prev, concept]
    );
  };

  const addCustomConcept = () => {
    const val = newCustomConcept.trim().toLowerCase();
    if (val && !concepts.includes(val) && !customConcepts.includes(val)) {
      setCustomConcepts([...customConcepts, val]);
      setNewCustomConcept("");
    }
  };

  const removeCustomConcept = (concept: string) => {
    setCustomConcepts(customConcepts.filter(c => c !== concept));
  };

  const addStdinScenario = () => {
    const nextId = stdinScenarios.length + 1;
    setStdinScenarios([...stdinScenarios, {
      key: `scenario_${nextId}`,
      label: `Scenario ${nextId}`,
      stdin: []
    }]);
  };

  const removeStdinScenario = (key: string) => {
    setStdinScenarios(stdinScenarios.filter(s => s.key !== key));
  };

  const updateStdinScenario = (key: string, field: "key" | "label" | "stdin", val: any) => {
    setStdinScenarios(prev => prev.map(s => {
      if (s.key === key) {
        let finalVal = val;
        if (field === "key") finalVal = sanitizeKey(val);
        return { ...s, [field]: finalVal };
      }
      return s;
    }));
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
    setDependencies(dependencies.filter(d => d !== dep));
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-500 font-medium animate-pulse">Loading assignment details...</p>
      </div>
    );
  }

  const allPossibleConcepts = [
    { key: "variables", desc: "Allows variable declarations and assignments (e.g. x = 5)." },
    { key: "conditionals", desc: "Allows comparison operators, if-else logic, and ternary statements." },
    { key: "loops", desc: "Allows iterative processing structures (for loops, while loops)." },
    { key: "functions", desc: "Allows declaring custom modular operations (def / async def statements)." },
    { key: "file-io", desc: "Allows opening, reading, or writing physical files (e.g. open(), read())." },
    { key: "image-processing", desc: "Allows importing and executing operations on the Pillow/PIL library." },
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
            <p className="text-slate-500">Configure parameters for assignment "{assignmentId}"</p>
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
            <TabsTrigger value="bundle">Step 2: Bundle</TabsTrigger>
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
                <CardDescription>
                  Modify the assignment name and control student sandbox features.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">Assignment Title *</label>
                    <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Project 1: Calculator" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold text-slate-700">Programming Language (Read-only)</label>
                    <Input value={setup?.language} disabled className="bg-slate-100 font-mono text-slate-500" />
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
                  <label htmlFor="sandbox" className="text-sm font-semibold text-slate-700 cursor-pointer">
                    Enable Student Sandbox Access
                  </label>
                </div>
                <p className="text-xs text-slate-400 pl-6">
                  Allows students to run tentative submissions against sandbox autograding checks before final lock-in.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* STEP 2: INGESTION FILES & LAYOUT */}
          <TabsContent value="bundle">
            <Card>
              <CardHeader>
                <CardTitle>Ingestion Files & Layout</CardTitle>
                <CardDescription>
                  Configure required files inside the student's submission zip and layout specifications.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                
                {/* Required Files list */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-slate-800">Required Submission Files</h3>
                  <p className="text-xs text-slate-400">Paths that must be present in the submission bundle zip file.</p>
                  
                  <TagBadgeList
                    tags={requiredFiles}
                    onRemove={removeRequiredFile}
                    emptyText="At least one required file is recommended."
                  />

                  <div className="flex gap-2 max-w-sm">
                    <Input
                      value={newRequiredFile}
                      onChange={(e) => setNewRequiredFile(e.target.value)}
                      placeholder="e.g. main.py"
                      className="font-mono text-sm"
                      onKeyDown={(e) => e.key === "Enter" && addRequiredFile()}
                    />
                    <Button type="button" onClick={addRequiredFile} variant="outline" size="sm">
                      <PlusIcon className="size-4 mr-1" /> Add Path
                    </Button>
                  </div>
                </div>

                {/* Entrypoint Selection */}
                <div className="space-y-2 pt-4 border-t border-slate-100 max-w-sm">
                  <label className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
                    Entrypoint Path *
                    <span title="The primary runnable Python script to execute during tests.">
                      <HelpCircleIcon className="size-3.5 text-slate-400" />
                    </span>
                  </label>
                  <p className="text-xs text-slate-400">Choose from required files or file requirement paths.</p>
                  <select
                    value={entrypoint}
                    onChange={(e) => setEntrypoint(e.target.value)}
                    className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none font-mono"
                  >
                    <option value="">-- Select Entrypoint --</option>
                    {getEntrypointOptions().map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>

                {/* File Requirements */}
                <div className="space-y-3 pt-6 border-t border-slate-100">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">Validation Rules (File Requirements)</h3>
                      <p className="text-xs text-slate-400">Optional pattern validations or path exclusions for submissions.</p>
                    </div>
                    <Button type="button" onClick={addFileRequirement} variant="outline" size="sm">
                      <PlusCircleIcon className="size-4 mr-1.5" /> Add Rule
                    </Button>
                  </div>

                  <div className="space-y-4">
                    {fileRequirements.map((req, idx) => (
                      <div key={idx} className="relative rounded-lg border border-slate-200 bg-white p-4 shadow-sm space-y-4">
                        <button
                          type="button"
                          onClick={() => removeFileRequirement(idx)}
                          className="absolute right-4 top-4 text-slate-400 hover:text-red-500 transition-colors cursor-pointer"
                        >
                          <Trash2Icon className="size-4" />
                        </button>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div className="space-y-1">
                            <label className="text-xs font-semibold text-slate-500 uppercase">Slug Key *</label>
                            <Input
                              value={req.key}
                              onChange={(e) => updateFileRequirement(idx, "key", e.target.value)}
                              placeholder="e.g. sol_file"
                              className="font-mono text-xs"
                            />
                            {!isValidKey(req.key) && (
                              <p className="text-[10px] text-red-500">Must be lowercase snake_case.</p>
                            )}
                          </div>
                          <div className="space-y-1">
                            <label className="text-xs font-semibold text-slate-500 uppercase">Label</label>
                            <Input
                              value={req.label || ""}
                              onChange={(e) => updateFileRequirement(idx, "label", e.target.value)}
                              placeholder="e.g. Main Solution File"
                              className="text-xs"
                            />
                          </div>
                          <div className="space-y-1">
                            <label className="text-xs font-semibold text-slate-500 uppercase">Requirement Type</label>
                            <select
                              value={req.requirement_type}
                              onChange={(e) => updateFileRequirement(idx, "requirement_type", e.target.value)}
                              className="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-xs focus:border-indigo-500 focus:outline-none font-mono"
                            >
                              <option value="exact">exact (Exactly 1 matching file)</option>
                              <option value="one_of">one_of (At least 1 from a set)</option>
                              <option value="optional">optional (0 or 1 matching file)</option>
                              <option value="pattern">pattern (Regex matcher path)</option>
                            </select>
                          </div>
                        </div>

                        {/* Paths management */}
                        <div className="space-y-2 pt-2 border-t border-slate-100">
                          <label className="text-xs font-semibold text-slate-500 uppercase">Target Path(s)</label>
                          {req.requirement_type === "one_of" ? (
                            <div className="space-y-2">
                              {req.paths.map((path, pathIdx) => (
                                <div key={pathIdx} className="flex gap-2 items-center">
                                  <Input
                                    value={path}
                                    onChange={(e) => updateFileRequirementPath(idx, pathIdx, e.target.value)}
                                    placeholder="e.g. solution.py"
                                    className="font-mono text-xs"
                                  />
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => removeFileRequirementPath(idx, pathIdx)}
                                    disabled={req.paths.length <= 1}
                                  >
                                    <XIcon className="size-3.5 text-slate-400 hover:text-red-500" />
                                  </Button>
                                </div>
                              ))}
                              <Button type="button" onClick={() => addFileRequirementPath(idx)} variant="link" size="sm" className="h-6 text-xs p-0 text-indigo-600">
                                <PlusIcon className="size-3 mr-1" /> Add Alternate Path
                              </Button>
                            </div>
                          ) : (
                            <Input
                              value={req.paths[0] || ""}
                              onChange={(e) => updateFileRequirementPath(idx, 0, e.target.value)}
                              placeholder={req.requirement_type === "pattern" ? "e.g. .*\\.py" : "e.g. solution.py"}
                              className="font-mono text-xs max-w-md"
                            />
                          )}
                        </div>
                      </div>
                    ))}
                    {fileRequirements.length === 0 && (
                      <p className="text-xs text-slate-400 italic">No custom file validation rules configured.</p>
                    )}
                  </div>
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
                  Configure autograded tests, manual rubric checks, and their visual groups.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">

                {/* Rubric Groups Management */}
                <div className="space-y-3 bg-slate-50 p-4 rounded-lg border border-slate-100">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">Rubric Group Headers</h3>
                      <p className="text-xs text-slate-500">Visual headings used in grading tables to group scoring items.</p>
                    </div>
                    <Button type="button" onClick={addRubricGroup} variant="outline" size="sm">
                      <PlusIcon className="size-4 mr-1" /> Add Group
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {rubricGroups.map((group) => (
                      <div key={group.key} className="flex gap-2 items-center bg-white p-2.5 rounded border border-slate-200 shadow-xs relative group-item">
                        <div className="grid grid-cols-2 gap-2 grow">
                          <Input
                            value={group.key}
                            onChange={(e) => updateRubricGroup(group.key, "key", e.target.value)}
                            placeholder="Slug Key"
                            className="text-xs font-mono"
                          />
                          <Input
                            value={group.label}
                            onChange={(e) => updateRubricGroup(group.key, "label", e.target.value)}
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
                      <p className="text-xs text-slate-400 italic col-span-2">No rubric groups created. Scoring items will be ungrouped.</p>
                    )}
                  </div>
                </div>

                {/* Autograded tests section */}
                <div className="space-y-2">
                  {setup?.artifacts.find(art => art.artifact_type === "pytest_file") && (
                    <div className="flex justify-end">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const art = setup?.artifacts.find(art => art.artifact_type === "pytest_file");
                          if (art) {
                            openCodeEditor(art.artifact_key, "pytest_file", art.display_filename || "test_suite.py");
                          }
                        }}
                      >
                        <FileTextIcon className="size-4 mr-1.5" /> Edit Test Code
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
                <CardTitle>Whitelist Concepts & Input Scenarios</CardTitle>
                <CardDescription>
                  Define what syntax structures are whitelisted and keyboard scenarios for interactive CLI tests.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">

                {/* Concepts Whitelist Checkbox grid */}
                <div className="space-y-3">
                  <h3 className="text-sm font-bold text-slate-800">Predefined Whitelisted Concepts</h3>
                  <p className="text-xs text-slate-400">Select standard programming syntax structures allowed in student submissions. Missing ones emit warnings.</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {allPossibleConcepts.map((item) => (
                      <div key={item.key} className="flex gap-2 items-start border border-slate-200/60 p-3 rounded-lg bg-white shadow-2xs">
                        <input
                          type="checkbox"
                          id={`concept-${item.key}`}
                          checked={concepts.includes(item.key)}
                          onChange={() => handleConceptChange(item.key)}
                          className="size-4 shrink-0 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 mt-0.5 cursor-pointer"
                        />
                        <div className="space-y-0.5">
                          <label htmlFor={`concept-${item.key}`} className="text-xs font-bold text-slate-700 uppercase cursor-pointer">
                            {item.key}
                          </label>
                          <p className="text-[11px] text-slate-400 leading-normal">{item.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Custom concepts additions */}
                <div className="space-y-3 pt-4 border-t border-slate-100">
                  <h3 className="text-sm font-bold text-slate-800">Custom Concepts Whitelist</h3>
                  <p className="text-xs text-slate-400">Add any other arbitrary custom concepts to log or analyze during submissions.</p>

                  <TagBadgeList
                    tags={customConcepts}
                    onRemove={removeCustomConcept}
                    emptyText="No custom whitelist concepts added."
                  />

                  <div className="flex gap-2 max-w-sm">
                    <Input
                      value={newCustomConcept}
                      onChange={(e) => setNewCustomConcept(e.target.value)}
                      placeholder="e.g. recursion"
                      className="text-sm"
                      onKeyDown={(e) => e.key === "Enter" && addCustomConcept()}
                    />
                    <Button type="button" onClick={addCustomConcept} variant="outline" size="sm">
                      <PlusIcon className="size-4 mr-1" /> Add
                    </Button>
                  </div>
                </div>

                {/* Stdin scenarios list */}
                <div className="space-y-4 pt-6 border-t border-slate-100">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-sm font-bold text-slate-800">Simulated Keyboard Scenarios (Stdin Scenarios)</h3>
                      <p className="text-xs text-slate-400">Preload text inputs to mimic sequential user keyboard lines for CLI programs.</p>
                    </div>
                    <Button type="button" onClick={addStdinScenario} variant="outline" size="sm">
                      <PlusCircleIcon className="size-4 mr-1.5" /> Add Scenario
                    </Button>
                  </div>

                  <div className="space-y-4">
                    {stdinScenarios.map((scenario, idx) => (
                      <div key={idx} className="relative rounded-lg border border-slate-200 bg-white p-4 shadow-sm space-y-3">
                        <button
                          type="button"
                          onClick={() => removeStdinScenario(scenario.key)}
                          className="absolute right-4 top-4 text-slate-400 hover:text-red-500 transition-colors cursor-pointer"
                        >
                          <Trash2Icon className="size-4" />
                        </button>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div className="space-y-1">
                            <label className="text-xs font-semibold text-slate-500 uppercase">Scenario Key *</label>
                            <Input
                              value={scenario.key}
                              onChange={(e) => updateStdinScenario(scenario.key, "key", e.target.value)}
                              placeholder="e.g. run_simple"
                              className="font-mono text-xs"
                            />
                            {!isValidKey(scenario.key) && (
                              <p className="text-[10px] text-red-500">Must be lowercase snake_case.</p>
                            )}
                          </div>
                          <div className="space-y-1">
                            <label className="text-xs font-semibold text-slate-500 uppercase">Scenario Student-Facing Description</label>
                            <Input
                              value={scenario.label}
                              onChange={(e) => updateStdinScenario(scenario.key, "label", e.target.value)}
                              placeholder="e.g. Enter positive numbers"
                              className="text-xs"
                            />
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          <label className="text-xs font-semibold text-slate-500 uppercase flex items-center gap-1">
                            Input Lines (one entry per line)
                            <span title="Simulates a user pressing Enter after typing each line.">
                              <HelpCircleIcon className="size-3 text-slate-400" />
                            </span>
                          </label>
                          <textarea
                            value={scenario.stdin.join("\n")}
                            onChange={(e) => updateStdinScenario(scenario.key, "stdin", e.target.value.split("\n"))}
                            placeholder="e.g.&#10;5&#10;10&#10;yes"
                            rows={3}
                            className="w-full font-mono text-xs rounded border border-slate-300 p-2 focus:border-indigo-500 focus:outline-none leading-relaxed"
                          />
                        </div>
                      </div>
                    ))}
                    {stdinScenarios.length === 0 && (
                      <p className="text-xs text-slate-400 italic">No simulated CLI keyboard scenarios configured.</p>
                    )}
                  </div>
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
                  List external Python package dependencies required by student code.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-800">Required Libraries</h3>
                  <p className="text-xs text-slate-400">Pip packages installed in sandbox containers prior to execution (e.g. numpy, pillow).</p>

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
                    <Button type="button" onClick={addDependency} variant="outline" size="sm">
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
                  Execute model solutions against the config suite. Ensure test parity.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Button onClick={triggerValidation} disabled={validation.status === "queue" || validation.status === "run"}>
                    <PlayIcon className="mr-2 size-4" /> Run Validation
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

        {/* Code Editor Modal Overlay */}
        {isCodeModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-fade-in">
            <div className="bg-white rounded-lg border border-slate-200 shadow-xl w-full max-w-5xl h-[85vh] flex flex-col">
              <div className="p-4 border-b border-slate-200 flex justify-between items-center bg-slate-50 rounded-t-lg">
                <div className="flex items-center gap-2">
                  <FileTextIcon className="size-5 text-indigo-600 animate-pulse" />
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">Editing Grading Code: {editArtifactFilename}</h3>
                    <p className="text-xs text-slate-400">Directly modify the test suite content on the server.</p>
                  </div>
                </div>
                <button type="button" onClick={() => setIsCodeModalOpen(false)} className="text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">
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
                  <p className="text-xs text-slate-400 animate-pulse font-mono">Fetching file content from server...</p>
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
                <Button variant="outline" size="sm" onClick={() => setIsCodeModalOpen(false)} disabled={isSavingCode}>
                  Cancel
                </Button>
                <Button size="sm" onClick={saveCodeChanges} disabled={isSavingCode}>
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
