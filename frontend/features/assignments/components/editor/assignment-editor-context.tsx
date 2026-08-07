"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { slugifyKey } from "@/lib/slugify";
import {
  deleteStaffAssignment,
  getConceptsMetadata,
} from "@/features/assignments/api";
import {
  StaffAssignmentSetup,
  StaffArtifact,
  RubricItem,
  RubricGroup,
  FileRequirementConfig,
  AssignmentConfigV1,
  ConceptMetadata,
} from "@/features/assignments/types";

type CourseModule = {
  id: number;
  name: string;
  concepts?: string[];
};

type CourseConceptsResponse = {
  course_id: string;
  default_concepts: string[];
  modules: CourseModule[];
};

type AssignmentEditorContextType = {
  courseId: string;
  assignmentId: string;
  loading: boolean;
  saving: boolean;
  dirty: boolean;
  saveSuccess: boolean;
  errorMessage: string | null;
  successMessage: string | null;
  setErrorMessage: (msg: string | null) => void;
  setSuccessMessage: (msg: string | null) => void;
  markDirty: () => void;

  // Metadata
  title: string;
  setTitle: (t: string) => void;
  moduleId: number | null;
  setModuleId: (m: number | null) => void;
  sandboxEnabled: boolean;
  setSandboxEnabled: (s: boolean) => void;
  language: string;

  // Bundle / File requirements
  entrypoint: string;
  setEntrypoint: (e: string) => void;
  fileRequirements: FileRequirementConfig[];
  addFileRequirement: () => void;
  removeFileRequirement: (idx: number) => void;
  updateFileRequirement: (idx: number, field: keyof FileRequirementConfig, val: unknown) => void;
  updateFileRequirementPath: (reqIdx: number, pathIdx: number, val: string) => void;
  addFileRequirementPath: (reqIdx: number) => void;
  removeFileRequirementPath: (reqIdx: number, pathIdx: number) => void;
  toggleFileRequirementGlob: (reqIdx: number, isGlob: boolean) => void;

  // Scoring items & rubric groups
  scoringItems: RubricItem[];
  addScoringItem: (itemType: "pytest" | "manual") => void;
  removeScoringItem: (key: string) => void;
  updateScoringItemField: (key: string, field: keyof RubricItem, val: unknown) => void;
  rubricGroups: RubricGroup[];
  addRubricGroup: () => void;
  removeRubricGroup: (key: string) => void;
  updateRubricGroup: (key: string, field: "key" | "label", val: string) => void;
  customKeyMap: Record<string, boolean>;
  toggleCustomKey: (key: string) => void;
  autoGenerateKeyFromLabel: (key: string) => void;
  syncMarkersFromTestSuite: (sourceCode: string) => number;


  // Concepts & Dependencies
  conceptDenylist: string[];
  toggleConceptDenylist: (conceptKey: string) => void;
  inheritedConcepts: string[];
  effectiveConcepts: string[];


  courseDefaultConcepts: string[];
  moduleConcepts: string[];
  conceptMeta: Record<string, ConceptMetadata>;
  courseModules: CourseModule[];
  dependencies: string[];
  addDependency: (dep: string) => void;
  removeDependency: (dep: string) => void;

  // Artifacts & Code Modal
  artifacts: StaffArtifact[];
  setArtifacts: React.Dispatch<React.SetStateAction<StaffArtifact[]>>;
  refreshArtifacts: () => Promise<void>;
  isCodeModalOpen: boolean;
  setIsCodeModalOpen: (open: boolean) => void;
  editArtifactKey: string | null;
  editArtifactFilename: string;
  editCodeText: string;
  setEditCodeText: (text: string) => void;
  isLoadingCode: boolean;
  isSavingCode: boolean;
  openCodeEditor: (key: string, type: string, filename: string) => Promise<void>;
  saveCodeChanges: () => Promise<void>;

  // Actions
  handleSave: () => Promise<void>;
  handleDelete: () => Promise<void>;
  handleCopyStudentLink: () => void;
  copiedLink: boolean;
};

const AssignmentEditorContext = createContext<AssignmentEditorContextType | null>(null);

export function AssignmentEditorProvider({
  courseId,
  assignmentId,
  children,
}: {
  courseId: string;
  assignmentId: string;
  children: React.ReactNode;
}) {
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // General Metadata
  const [title, setTitle] = useState("");
  const [moduleId, setModuleId] = useState<number | null>(null);
  const [sandboxEnabled, setSandboxEnabled] = useState(true);
  const [language, setLanguage] = useState("python");

  // Bundle / File requirements
  const [entrypoint, setEntrypoint] = useState("main.py");
  const [fileRequirements, setFileRequirements] = useState<FileRequirementConfig[]>([
    { label: "Main Entrypoint Script", paths: ["main.py"] },
  ]);

  // Scoring & Rubrics
  const [scoringItems, setScoringItems] = useState<RubricItem[]>([]);
  const [rubricGroups, setRubricGroups] = useState<RubricGroup[]>([]);
  const [customKeyMap, setCustomKeyMap] = useState<Record<string, boolean>>({});

  // Concepts & Dependencies
  const [conceptDenylist, setConceptDenylist] = useState<string[]>([]);
  const [courseDefaultConcepts, setCourseDefaultConcepts] = useState<string[]>([]);
  const [conceptMeta, setConceptMeta] = useState<Record<string, ConceptMetadata>>({});
  const [courseModules, setCourseModules] = useState<CourseModule[]>([]);
  const [dependencies, setDependencies] = useState<string[]>([]);

  const moduleConcepts = useMemo(() => {
    if (moduleId === null) return [];
    const mod = courseModules.find((m) => m.id === moduleId);
    return mod?.concepts || [];
  }, [moduleId, courseModules]);

  // Dynamically compute cumulative inherited concepts up to currently selected moduleId
  const inheritedConcepts = useMemo(() => {
    const seen = new Set<string>();
    const out: string[] = [];

    (courseDefaultConcepts || []).forEach((c) => {
      if (!seen.has(c)) {
        seen.add(c);
        out.push(c);
      }
    });

    if (moduleId !== null && courseModules.length > 0) {
      const sortedMods = [...courseModules].sort((a, b) => (a.id || 0) - (b.id || 0));
      for (const m of sortedMods) {
        (m.concepts || []).forEach((c) => {
          if (!seen.has(c)) {
            seen.add(c);
            out.push(c);
          }
        });
        if (m.id === moduleId) break;
      }
    }

    return out;
  }, [courseDefaultConcepts, courseModules, moduleId]);

  const effectiveConcepts = useMemo(() => {
    const denyset = new Set(conceptDenylist || []);
    return inheritedConcepts.filter((c) => !denyset.has(c));
  }, [inheritedConcepts, conceptDenylist]);

  // Artifacts
  const [artifacts, setArtifacts] = useState<StaffArtifact[]>([]);
  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [editArtifactKey, setEditArtifactKey] = useState<string | null>(null);
  const [editArtifactType, setEditArtifactType] = useState<string>("pytest_file");
  const [editArtifactFilename, setEditArtifactFilename] = useState("");
  const [editCodeText, setEditCodeText] = useState("");
  const [isLoadingCode, setIsLoadingCode] = useState(false);
  const [isSavingCode, setIsSavingCode] = useState(false);

  // Link copy
  const [copiedLink, setCopiedLink] = useState(false);

  const markDirty = () => {
    setDirty(true);
    setSaveSuccess(false);
    setSuccessMessage(null);
  };

  // Load configuration and data
  const loadSetup = useCallback(async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [setupData, metaData, courseConcepts] = await Promise.all([
        apiClient.get<StaffAssignmentSetup>(`/staff/courses/${courseId}/assignments/${assignmentId}/setup`),
        getConceptsMetadata(),
        apiClient.get<CourseConceptsResponse>(`/staff/courses/${courseId}/concepts`),
      ]);

      setTitle(setupData.title || "");
      setModuleId(setupData.module_id ?? null);
      setSandboxEnabled(setupData.sandbox_enabled ?? true);
      setLanguage(setupData.language || "python");
      setArtifacts(setupData.artifacts || []);
      setConceptMeta(metaData || {});
      setCourseDefaultConcepts(courseConcepts.default_concepts || []);
      setCourseModules(courseConcepts.modules || []);

      const cfg = setupData.config_json || ({} as AssignmentConfigV1);
      const bundle = cfg.bundle || { entrypoint: "main.py" };
      setEntrypoint(bundle.entrypoint || "main.py");

      if (bundle.file_requirements && bundle.file_requirements.length > 0) {
        setFileRequirements(bundle.file_requirements);
      } else {
        setFileRequirements([{ label: "Main Entrypoint Script", paths: [bundle.entrypoint || "main.py"] }]);
      }

      setScoringItems(cfg.scoring_items || setupData.scoring_items || []);
      setRubricGroups(cfg.rubric_groups || setupData.rubric_groups || []);
      setDependencies(cfg.dependencies || []);
      const legacyConcepts = cfg.concepts as Record<string, string[]> | undefined;
      setConceptDenylist(cfg.concepts?.denylist || legacyConcepts?.blacklist || []);

      setDirty(false);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load assignment setup.");
    } finally {
      setLoading(false);
    }
  }, [courseId, assignmentId]);

  useEffect(() => {
    let active = true;
    const run = async () => {
      await loadSetup();
    };
    if (active) run();
    return () => {
      active = false;
    };
  }, [loadSetup]);


  const refreshArtifacts = async () => {
    try {
      const res = await apiClient.get<StaffAssignmentSetup>(
        `/staff/courses/${courseId}/assignments/${assignmentId}/setup`
      );
      setArtifacts(res.artifacts || []);
    } catch {
      // ignore refresh errors
    }
  };

  // File requirement helpers
  const addFileRequirement = () => {
    const nextId = fileRequirements.length + 1;
    setFileRequirements((prev) => [...prev, { label: `Required File Rule ${nextId}`, paths: [""] }]);
    markDirty();
  };

  const removeFileRequirement = (idx: number) => {
    setFileRequirements((prev) => prev.filter((_, i) => i !== idx));
    markDirty();
  };

  const updateFileRequirement = (idx: number, field: keyof FileRequirementConfig, val: unknown) => {
    setFileRequirements((prev) => prev.map((req, i) => (i === idx ? { ...req, [field]: val } : req)));
    markDirty();
  };

  const updateFileRequirementPath = (reqIdx: number, pathIdx: number, val: string) => {
    setFileRequirements((prev) =>
      prev.map((req, i) => {
        if (i === reqIdx) {
          const currentPaths = req.paths || [""];
          const newPaths = [...currentPaths];
          newPaths[pathIdx] = val;
          return { ...req, paths: newPaths };
        }
        return req;
      })
    );
    markDirty();
  };

  const addFileRequirementPath = (reqIdx: number) => {
    setFileRequirements((prev) =>
      prev.map((req, i) => {
        if (i === reqIdx) {
          const currentPaths = req.paths || [""];
          return { ...req, paths: [...currentPaths, ""] };
        }
        return req;
      })
    );
    markDirty();
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
      })
    );
    markDirty();
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
      })
    );
    markDirty();
  };

  // Scoring items mutators
  const toggleCustomKey = (key: string) => {
    setCustomKeyMap((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const addScoringItem = (itemType: "pytest" | "manual") => {
    const nextId = scoringItems.length + 1;
    const baseKey = `${itemType}_item_${nextId}`;
    const newItem: RubricItem = {
      key: baseKey,
      label: itemType === "pytest" ? `Pytest Criterion ${nextId}` : `Manual Rubric Item ${nextId}`,
      points: 10,
      extra_credit: false,
      item_type: itemType,
      pytest_marker: itemType === "pytest" ? `ag_${baseKey}` : null,
      rubric_group_key: null,
    };
    setScoringItems((prev) => [...prev, newItem]);
    markDirty();
  };

  const removeScoringItem = (key: string) => {
    setScoringItems((prev) => prev.filter((item) => item.key !== key));
    markDirty();
  };

  const updateScoringItemField = (key: string, field: keyof RubricItem, val: unknown) => {
    setScoringItems((prev) =>
      prev.map((item) => {
        if (item.key === key) {
          const updated = { ...item, [field]: val };
          if (field === "key") {
            const raw = String(val).toLowerCase().replace(/[^a-z0-9_]/g, "");
            updated.key = raw;
            if (updated.item_type === "pytest") {
              updated.pytest_marker = `ag_${raw}`;
            }
          }
          return updated;
        }
        return item;
      })
    );
    markDirty();
  };

  const autoGenerateKeyFromLabel = (key: string) => {
    setScoringItems((prev) =>
      prev.map((item) => {
        if (item.key === key) {
          const derived = slugifyKey(item.label);
          if (derived) {
            const updated = { ...item, key: derived };
            if (updated.item_type === "pytest") {
              updated.pytest_marker = `ag_${derived}`;
            }
            return updated;
          }
        }
        return item;
      })
    );
    markDirty();
  };

  // Rubric groups mutators
  const addRubricGroup = () => {
    const nextId = rubricGroups.length + 1;
    const key = `group_${nextId}`;
    setRubricGroups((prev) => [...prev, { key, label: `Group ${nextId}` }]);
    markDirty();
  };

  const removeRubricGroup = (key: string) => {
    setRubricGroups((prev) => prev.filter((g) => g.key !== key));
    setScoringItems((prev) =>
      prev.map((item) => (item.rubric_group_key === key ? { ...item, rubric_group_key: null } : item))
    );
    markDirty();
  };

  const updateRubricGroup = (key: string, field: "key" | "label", val: string) => {
    const updatedVal = field === "key" ? slugifyKey(val) : val;
    setRubricGroups((prev) =>
      prev.map((g) => (g.key === key ? { ...g, [field]: updatedVal } : g))
    );
    if (field === "key") {
      setScoringItems((prev) =>
        prev.map((item) => (item.rubric_group_key === key ? { ...item, rubric_group_key: updatedVal } : item))
      );
    }
    markDirty();
  };

  const toggleConceptDenylist = (conceptKey: string) => {
    setConceptDenylist((prev) =>
      prev.includes(conceptKey) ? prev.filter((c) => c !== conceptKey) : [...prev, conceptKey]
    );
    markDirty();
  };


  const parseExpectedIO = (sourceCode: string, key: string) => {
    const inputs: string[] = [];
    const outputs: string[] = [];

    // Match block following marker up to next marker or end of code
    const markerRegex = new RegExp(`@(?:pytest\\.)?(?:mark\\.)?ag_${key}\\b([\\s\\S]*?)(?=(?:@(?:pytest\\.)?(?:mark\\.)?ag_|\\Z))`, "i");
    const match = sourceCode.match(markerRegex);
    const block = match ? match[1] : sourceCode;

    const inputMatches = block.matchAll(/EXPECTED_INPUT(?:S)?\s*=\s*(?:["']{3}([\s\S]*?)["']{3}|["']([^"'\r\n]*)["'])/g);
    for (const m of inputMatches) {
      const val = m[1] !== undefined ? m[1] : m[2];
      if (val && !inputs.includes(val.trim())) inputs.push(val.trim());
    }

    const outputMatches = block.matchAll(/EXPECTED_OUTPUT(?:S)?\s*=\s*(?:["']{3}([\s\S]*?)["']{3}|["']([^"'\r\n]*)["'])/g);
    for (const m of outputMatches) {
      const val = m[1] !== undefined ? m[1] : m[2];
      if (val && !outputs.includes(val.trim())) outputs.push(val.trim());
    }

    return {
      inputs: inputs.length > 0 ? inputs : undefined,
      outputs: outputs.length > 0 ? outputs : undefined,
    };
  };

  const syncMarkersFromTestSuite = (sourceCode: string) => {
    const matches = sourceCode.match(/@(?:pytest\.)?(?:mark\.)?ag_([a-zA-Z0-9_]+)/g);
    if (!matches) return 0;

    const extractedKeys = Array.from(
      new Set(matches.map((m) => m.replace(/^.*ag_/, "")))
    );

    let addedCount = 0;
    setScoringItems((prev) => {
      const existingKeys = new Set(prev.map((item) => item.key));
      const updatedItems = prev.map((item) => {
        if (extractedKeys.includes(item.key) && (item.item_type || "pytest") === "pytest") {
          const parsed = parseExpectedIO(sourceCode, item.key);
          return {
            ...item,
            inputs: parsed.inputs || item.inputs,
            outputs: parsed.outputs || item.outputs,
          };
        }
        return item;
      });

      const newItems: RubricItem[] = [];
      extractedKeys.forEach((k) => {
        if (!existingKeys.has(k)) {
          addedCount++;
          const parsed = parseExpectedIO(sourceCode, k);
          newItems.push({
            key: k,
            label: `${k.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())} Test`,
            points: 10,
            extra_credit: false,
            item_type: "pytest",
            pytest_marker: `ag_${k}`,
            rubric_group_key: null,
            inputs: parsed.inputs,
            outputs: parsed.outputs,
          });
        }
      });

      if (addedCount > 0 || newItems.length > 0) {
        markDirty();
      }
      return [...updatedItems, ...newItems];
    });

    return addedCount;
  };

  const addDependency = (dep: string) => {


    const trimmed = dep.trim();
    if (trimmed && !dependencies.includes(trimmed)) {
      setDependencies((prev) => [...prev, trimmed]);
      markDirty();
    }
  };

  const removeDependency = (dep: string) => {
    setDependencies((prev) => prev.filter((d) => d !== dep));
    markDirty();
  };

  // Code editor modal mutators
  const openCodeEditor = async (key: string, type: string, filename: string) => {
    setErrorMessage(null);
    setEditArtifactKey(key);
    setEditArtifactType(type);
    setEditArtifactFilename(filename);
    setEditCodeText("");
    setIsCodeModalOpen(true);
    setIsLoadingCode(true);

    try {
      const text = await apiClient.getText(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${key}`
      );
      setEditCodeText(text);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to fetch artifact code.");
    } finally {
      setIsLoadingCode(false);
    }
  };

  const saveCodeChanges = async () => {
    if (!editArtifactKey) return;
    setIsSavingCode(true);
    try {
      const file = new File([editCodeText], editArtifactFilename, { type: "text/plain" });
      const formData = new FormData();
      formData.append("file", file);
      formData.append("artifact_key", editArtifactKey);
      formData.append("artifact_type", editArtifactType);

      await apiClient.postForm(`/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`, formData);
      setIsCodeModalOpen(false);
      setSuccessMessage(`Saved artifact '${editArtifactFilename}' successfully.`);
      await refreshArtifacts();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to save artifact code.");
    } finally {
      setIsSavingCode(false);
    }
  };

  // Save full assignment setup
  const handleSave = async () => {
    setSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      // Build artifacts dict for config_json reference check
      const artifactsDict: Record<string, { type: "pytest_file" | "model_solution" | "support_file"; display_filename?: string }> = {};
      artifacts.forEach((art) => {
        const artType = (["pytest_file", "model_solution", "support_file"].includes(art.artifact_type)
          ? art.artifact_type
          : "support_file") as "pytest_file" | "model_solution" | "support_file";
        artifactsDict[art.artifact_key] = {
          type: artType,
          display_filename: art.display_filename || undefined,
        };
      });

      if (!artifactsDict["assignment_tests"]) {
        artifactsDict["assignment_tests"] = { type: "pytest_file", display_filename: "test_assignment.py" };
      }


      const derivedRubricGroups = rubricGroups.length > 0
        ? rubricGroups
        : scoringItems.map((item) => ({ key: item.key, label: item.label }));

      const configJson: AssignmentConfigV1 = {
        bundle: {
          entrypoint,
          file_requirements: fileRequirements,
        },
        artifacts: artifactsDict,
        scoring_items: scoringItems,
        rubric_groups: derivedRubricGroups,
        dependencies,
        concepts: {
          allowlist: [],
          denylist: conceptDenylist,
        },
      };


      await apiClient.put(`/staff/courses/${courseId}/assignments/${assignmentId}/setup`, {
        title,
        sandbox_enabled: sandboxEnabled,
        module_id: moduleId,
        config_json: configJson,
      });

      setSaveSuccess(true);
      setDirty(false);
      setSuccessMessage("Assignment configuration saved successfully.");
      await loadSetup();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to save assignment configuration.");
    } finally {
      setSaving(false);
    }
  };

  // Delete assignment
  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete assignment "${assignmentId}"? This will deactivate the assignment.`)) {
      return;
    }
    try {
      await deleteStaffAssignment(courseId, assignmentId);
      router.push(`/staff/courses/${courseId}/assignments`);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to delete assignment.");
    }
  };

  // Copy student link
  const handleCopyStudentLink = () => {
    const url = `${window.location.origin}/sandbox/${courseId}/assignments/${assignmentId}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  return (
    <AssignmentEditorContext.Provider
      value={{
        courseId,
        assignmentId,
        loading,
        saving,
        dirty,
        saveSuccess,
        errorMessage,
        successMessage,
        setErrorMessage,
        setSuccessMessage,
        markDirty,

        title,
        setTitle,
        moduleId,
        setModuleId,
        sandboxEnabled,
        setSandboxEnabled,
        language,

        entrypoint,
        setEntrypoint,
        fileRequirements,
        addFileRequirement,
        removeFileRequirement,
        updateFileRequirement,
        updateFileRequirementPath,
        addFileRequirementPath,
        removeFileRequirementPath,
        toggleFileRequirementGlob,

        scoringItems,
        addScoringItem,
        removeScoringItem,
        updateScoringItemField,
        rubricGroups,
        addRubricGroup,
        removeRubricGroup,
        updateRubricGroup,
        customKeyMap,
        toggleCustomKey,
        autoGenerateKeyFromLabel,
        syncMarkersFromTestSuite,


        conceptDenylist,
        toggleConceptDenylist,
        inheritedConcepts,
        effectiveConcepts,


        courseDefaultConcepts,
        moduleConcepts,
        conceptMeta,
        courseModules,
        dependencies,
        addDependency,
        removeDependency,

        artifacts,
        setArtifacts,
        refreshArtifacts,
        isCodeModalOpen,
        setIsCodeModalOpen,
        editArtifactKey,
        editArtifactFilename,
        editCodeText,
        setEditCodeText,
        isLoadingCode,
        isSavingCode,
        openCodeEditor,
        saveCodeChanges,

        handleSave,
        handleDelete,
        handleCopyStudentLink,
        copiedLink,
      }}
    >
      {children}
    </AssignmentEditorContext.Provider>
  );
}

export function useAssignmentEditor() {
  const ctx = useContext(AssignmentEditorContext);
  if (!ctx) {
    throw new Error("useAssignmentEditor must be used within AssignmentEditorProvider");
  }
  return ctx;
}
