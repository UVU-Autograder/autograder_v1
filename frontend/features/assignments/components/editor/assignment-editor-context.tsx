"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { slugifyKey, makeUniqueKey } from "@/lib/slugify";
import {
  deleteStaffAssignment,
  getConceptsMetadata,
  syncStaffTests,
} from "@/features/assignments/api";
import {
  StaffAssignmentSetup,
  StaffArtifact,
  RubricItem,
  RubricGroup,
  FileRequirementConfig,
  AssignmentConfigV1,
  ConceptMetadata,
  ArtifactType,
  TestFramework,
  TEST_FRAMEWORKS_BY_LANGUAGE,
  defaultFrameworkForLanguage,
  defaultSuiteFilename,
  pytestMarkerForKey,
} from "@/features/assignments/types";

const PYTHON_STUB = `import pytest\n\n# Prefer ordinary imports of student modules, e.g. \`import main\`.\n# Use View Python helpers only for collisions, import-time input(), or long CLI mocks.\n\n\n@pytest.mark.ag_main\ndef test_main_function():\n    import main\n\n    assert hasattr(main, "__name__"), "Expected the submission module to import cleanly."\n`;

const GTEST_STUB = `#include <gtest/gtest.h>\n\n// Declare the public interface supplied by the student's implementation.\n// For C assignments, wrap C declarations/includes in extern "C" { ... }.\nextern int add(int, int);\n\nTEST(Assignment, ag_main) {\n    EXPECT_EQ(add(2, 3), 5);\n}\n`;

const JSDOM_STUB = `module.exports = ({ test, loadSubmission, assert }) => {\n  test('main', 'page has a heading', async () => {\n    const { document } = await loadSubmission();\n    assert.ok(document.querySelector('h1'), 'The page needs an h1 heading.');\n  });\n};\n`;

/** Starter suite for a missing test file. Never returns Python code for non-pytest frameworks. */
function starterSuite(framework: TestFramework): string {
  if (framework === "pytest") return PYTHON_STUB;
  if (framework === "gtest") return GTEST_STUB;
  if (framework === "jsdom") return JSDOM_STUB;
  return "";
}

function resolveFramework(language: string, candidate: TestFramework | undefined): TestFramework {
  const allowed = TEST_FRAMEWORKS_BY_LANGUAGE[language];
  return candidate && allowed?.includes(candidate) ? candidate : defaultFrameworkForLanguage(language);
}

function isSuiteArtifact(a: StaffArtifact): boolean {
  return a.artifact_type === "pytest_file" || a.artifact_type === "test_file";
}

function isCompatibleSuite(artifact: StaffArtifact, framework: TestFramework): boolean {
  const filename = artifact.display_filename?.toLowerCase() || "";
  if (framework === "pytest") return artifact.artifact_type === "pytest_file";
  if (artifact.artifact_type !== "test_file") return false;
  if (framework === "gtest") return /\.(cpp|cc|cxx|c)$/.test(filename);
  return framework === "jsdom" && /\.(cjs|js|mjs)$/.test(filename);
}

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

export type AssignmentEditorContextType = {
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
  handleDiscard: () => Promise<void>;

  // Metadata
  title: string;
  setTitle: (t: string) => void;
  canvasRef: string;
  setCanvasRef: (reference: string) => void;
  description: string;
  setDescription: (d: string) => void;
  moduleId: number | null;
  setModuleId: (m: number | null) => void;
  sandboxEnabled: boolean;
  setSandboxEnabled: (s: boolean) => void;
  language: string;
  setLanguage: (l: string) => void;
  testFramework: TestFramework;
  setTestFramework: (f: TestFramework) => void;

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
  /**
   * Python only: asks the backend to parse the suite and merges the result into scoring items.
   * Resolves to the number of newly added items, or null when nothing was applied (error surfaced).
   */
  syncTestsFromSource: (sourceCode: string) => Promise<number | null>;


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

  // Artifacts & Code Modal
  artifacts: StaffArtifact[];
  setArtifacts: React.Dispatch<React.SetStateAction<StaffArtifact[]>>;
  refreshArtifacts: () => Promise<void>;
  testSuiteCode: string;
  updateTestSuiteCode: (code: string) => void;
  loadingTestSuiteCode: boolean;
  isCodeModalOpen: boolean;
  setIsCodeModalOpen: (open: boolean) => void;
  editArtifactKey: string | null;
  editArtifactFilename: string;
  editCodeText: string;
  setEditCodeText: (text: string) => void;
  isLoadingCode: boolean;
  isSavingCode: boolean;
  openCodeEditor: (key: string, type: string, filename: string, initialText?: string) => Promise<void>;
  saveCodeChanges: () => Promise<void>;

  // Actions
  handleSave: () => Promise<void>;
  handleDelete: () => Promise<void>;
  handleCopyStudentLink: () => void;
  copiedLink: boolean;
};

export const AssignmentEditorContext = createContext<AssignmentEditorContextType | null>(null);

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
  const [canvasRef, setCanvasRef] = useState("");
  const [description, setDescription] = useState("");
  const [moduleId, setModuleId] = useState<number | null>(null);
  const [sandboxEnabled, setSandboxEnabled] = useState(true);
  const [language, setLanguageState] = useState("python");
  const [testFrameworkChoice, setTestFrameworkChoice] = useState<TestFramework | undefined>(undefined);
  const testFramework = resolveFramework(language, testFrameworkChoice);

  // Bundle / File requirements
  const [entrypoint, setEntrypoint] = useState("main.py");
  const [fileRequirements, setFileRequirements] = useState<FileRequirementConfig[]>([
    { paths: ["main.py"] },
  ]);

  // Scoring & Rubrics
  const [scoringItems, setScoringItems] = useState<RubricItem[]>([]);
  const [rubricGroups, setRubricGroups] = useState<RubricGroup[]>([]);

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

  // Artifacts & Test Suite Code
  const [artifacts, setArtifacts] = useState<StaffArtifact[]>([]);
  const [testSuiteCode, setTestSuiteCode] = useState("");
  const [loadingTestSuiteCode, setLoadingTestSuiteCode] = useState(true);
  const [testSuiteDirty, setTestSuiteDirty] = useState(false);
  const suiteLoadRef = useRef(0);
  const suiteDraftsRef = useRef<Partial<Record<TestFramework, string>>>({});
  const [isCodeModalOpen, setIsCodeModalOpen] = useState(false);
  const [editArtifactKey, setEditArtifactKey] = useState<string | null>(null);
  const [editArtifactType, setEditArtifactType] = useState<string>("pytest_file");
  const [editArtifactFilename, setEditArtifactFilename] = useState("");
  const [editCodeText, setEditCodeText] = useState("");
  const [isLoadingCode, setIsLoadingCode] = useState(false);
  const [isSavingCode, setIsSavingCode] = useState(false);

  // Link copy
  const [copiedLink, setCopiedLink] = useState(false);

  // Snapshot of last loaded/saved setup so reverting clears "Unsaved changes".
  const savedSnapshotRef = useRef<string | null>(null);
  const pendingBaselineRef = useRef(true);
  const loadedConfigRef = useRef<AssignmentConfigV1 | null>(null);

  const buildSnapshot = useCallback(() => {
    return JSON.stringify({
      title,
      canvasRef,
      description,
      moduleId,
      sandboxEnabled,
      language,
      testFramework,
      entrypoint,
      fileRequirements,
      scoringItems: scoringItems.map((item) => {
        const copy = { ...item };
        delete copy.id;
        return copy;
      }),
      rubricGroups,
      conceptDenylist,
      dependencies,
      testSuiteCode,
    });
  }, [
    title,
    canvasRef,
    description,
    moduleId,
    sandboxEnabled,
    language,
    testFramework,
    entrypoint,
    fileRequirements,
    scoringItems,
    rubricGroups,
    conceptDenylist,
    dependencies,
    testSuiteCode,
  ]);

  const markDirty = () => {
    setSaveSuccess(false);
    setSuccessMessage(null);
  };

  const updateTestSuiteCode = (nextCode: string) => {
    setTestSuiteCode(nextCode);
    setTestSuiteDirty(true);
    markDirty();
  };

  useEffect(() => {
    if (loading) return;
    if (pendingBaselineRef.current) {
      savedSnapshotRef.current = buildSnapshot();
      pendingBaselineRef.current = false;
      setDirty(false);
      return;
    }
    if (savedSnapshotRef.current === null) return;
    const nextDirty = buildSnapshot() !== savedSnapshotRef.current;
    setDirty(nextDirty);
    if (!nextDirty) {
      setSaveSuccess(false);
    }
  }, [loading, buildSnapshot]);

  // Load configuration and data
  const loadSetup = useCallback(async () => {
    suiteLoadRef.current++;
    setLoading(true);
    pendingBaselineRef.current = true;
    setErrorMessage(null);
    try {
      const [setupData, metaData, courseConcepts] = await Promise.all([
        apiClient.get<StaffAssignmentSetup>(`/staff/courses/${courseId}/assignments/${assignmentId}/setup`),
        getConceptsMetadata(),
        apiClient.get<CourseConceptsResponse>(`/staff/courses/${courseId}/concepts`),
      ]);

      const loadedArtifacts = setupData.artifacts || [];
      suiteDraftsRef.current = {};
      setTitle(setupData.title || "");
      setCanvasRef(setupData.canvas_ref || "");
      setDescription(setupData.description || setupData.config?.description || "");
      setModuleId(setupData.module_id ?? null);
      setSandboxEnabled(setupData.sandbox_enabled ?? true);
      const loadedLanguage = setupData.language || "python";
      const loadedFramework = resolveFramework(loadedLanguage, setupData.config?.test_framework);
      setLanguageState(loadedLanguage);
      setTestFrameworkChoice(loadedFramework);
      setArtifacts(loadedArtifacts);
      setConceptMeta(metaData || {});
      setCourseDefaultConcepts(courseConcepts.default_concepts || []);
      setCourseModules(courseConcepts.modules || []);

      const suiteArtifact = loadedArtifacts.find((artifact) => isCompatibleSuite(artifact, loadedFramework));
      setLoadingTestSuiteCode(true);
      try {
        if (suiteArtifact) {
          const text = await apiClient.getText(
            `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${suiteArtifact.artifact_key}`
          );
          setTestSuiteCode(text);
        } else {
          setTestSuiteCode(starterSuite(loadedFramework));
        }
      } catch {
        setTestSuiteCode(starterSuite(loadedFramework));
      } finally {
        setLoadingTestSuiteCode(false);
      }
      setTestSuiteDirty(false);

      const cfg = setupData.config || ({} as AssignmentConfigV1);
      loadedConfigRef.current = cfg;
      const bundle = cfg.bundle || { entrypoint: "main.py" };
      setEntrypoint(bundle.entrypoint || "main.py");

      if (bundle.file_requirements && bundle.file_requirements.length > 0) {
        setFileRequirements(bundle.file_requirements);
      } else {
        setFileRequirements([{ paths: [bundle.entrypoint || "main.py"] }]);
      }

      const rawItems = cfg.scoring_items || setupData.scoring_items || [];
      const defaultMode = cfg.comparison_mode || "normalized";
      const defaultTol = cfg.tolerance !== undefined ? cfg.tolerance : null;
      const loadedItems = rawItems.map((item: RubricItem, idx: number) => ({
        ...item,
        comparison_mode: item.comparison_mode || defaultMode,
        tolerance: item.tolerance !== undefined ? item.tolerance : defaultTol,
        id: item.id || `item_${item.key || idx}_${Math.random().toString(36).slice(2, 9)}`,
      }));
      setScoringItems(loadedItems);
      setRubricGroups(cfg.rubric_groups || setupData.rubric_groups || []);
      setDependencies(cfg.dependencies || []);
      const legacyConcepts = cfg.concepts as Record<string, string[]> | undefined;
      setConceptDenylist(cfg.concepts?.denylist || legacyConcepts?.blacklist || []);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load assignment setup.");
    } finally {
      setLoading(false);
    }
  }, [courseId, assignmentId]);

  const handleDiscard = useCallback(async () => {
    if (!dirty) return;
    await loadSetup();
  }, [dirty, loadSetup]);

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
    setFileRequirements((prev) => [...prev, { paths: [""] }]);
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
            return { pattern: "*.py" };
          } else {
            const firstPath = req.paths?.[0] || "";
            return { paths: [firstPath] };
          }
        }
        return req;
      })
    );
    markDirty();
  };

  // Scoring items mutators
  const addScoringItem = (itemType: "pytest" | "manual") => {
    const nextId = scoringItems.length + 1;
    const basePrefix = itemType === "pytest" ? `pytest_criterion_${nextId}` : `manual_criterion_${nextId}`;
    const uniqueKey = makeUniqueKey(basePrefix, scoringItems.map((i) => i.key));
    const newItem: RubricItem = {
      id: `rubric_item_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      key: uniqueKey,
      label: itemType === "pytest" ? `Pytest Criterion ${nextId}` : `Manual Rubric Item ${nextId}`,
      points: 10,
      extra_credit: false,
      is_private: false,
      item_type: itemType,
      pytest_marker: itemType === "pytest" ? pytestMarkerForKey(uniqueKey) : null,
      rubric_group_key: null,
      comparison_mode: "normalized",
      tolerance: null,
    };
    setScoringItems((prev) => [...prev, newItem]);
    markDirty();
  };

  const removeScoringItem = (keyOrId: string) => {
    setScoringItems((prev) => prev.filter((item) => item.id !== keyOrId && item.key !== keyOrId));
    markDirty();
  };

  const updateScoringItemField = (keyOrId: string, field: keyof RubricItem, val: unknown) => {
    setScoringItems((prev) => {
      const existingKeys = prev.map((i) => i.key);
      return prev.map((item) => {
        if (item.id === keyOrId || item.key === keyOrId) {
          const updated = { ...item, [field]: val };
          if (field === "key") {
            const raw = String(val).toLowerCase().replace(/[^a-z0-9_]/g, "");
            updated.key = raw;
            if (updated.item_type === "pytest") {
              updated.pytest_marker = pytestMarkerForKey(raw);
            }
          } else if (field === "label" && item.item_type === "manual") {
            const derived = slugifyKey(String(val));
            if (derived) {
              updated.key = makeUniqueKey(derived, existingKeys, item.key);
            }
          }
          return updated;
        }
        return item;
      });
    });
    markDirty();
  };

  const toggleConceptDenylist = (conceptKey: string) => {
    setConceptDenylist((prev) =>
      prev.includes(conceptKey) ? prev.filter((c) => c !== conceptKey) : [...prev, conceptKey]
    );
    markDirty();
  };


  const setTestFramework = (framework: TestFramework) => {
    setTestFrameworkChoice(framework);
    if (framework !== testFramework) {
      const loadId = ++suiteLoadRef.current;
      if (testSuiteDirty) suiteDraftsRef.current[testFramework] = testSuiteCode;
      const draft = suiteDraftsRef.current[framework];
      const artifact = artifacts.find((item) => isCompatibleSuite(item, framework));
      setTestSuiteCode(draft ?? starterSuite(framework));
      setTestSuiteDirty(draft !== undefined);
      setLoadingTestSuiteCode(Boolean(artifact) && draft === undefined);
      if (artifact && draft === undefined) {
        void apiClient.getText(
          `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${artifact.artifact_key}`,
        ).then((source) => {
          if (suiteLoadRef.current === loadId) setTestSuiteCode(source);
        }).catch(() => {
          if (suiteLoadRef.current === loadId) setErrorMessage("Could not load the test suite. Reload before editing it.");
        }).finally(() => {
          if (suiteLoadRef.current === loadId) setLoadingTestSuiteCode(false);
        });
      }
    }
    markDirty();
  };

  const setLanguage = (nextLanguage: string) => {
    setLanguageState(nextLanguage);
    setTestFramework(resolveFramework(nextLanguage, testFrameworkChoice));
  };

  const syncTestsFromSource = async (sourceCode: string): Promise<number | null> => {
    if (language !== "python") return null;
    setErrorMessage(null);
    let response;
    try {
      response = await syncStaffTests(courseId, assignmentId, sourceCode);
    } catch (err: unknown) {
      // Nothing is merged on failure (e.g. 422 for invalid Python), so the rubric is never half-updated.
      setErrorMessage(err instanceof Error ? err.message : "Failed to sync tests.");
      return null;
    }

    const synced = response.items || [];
    const existingKeys = new Set(scoringItems.map((item) => item.key));
    const addedCount = new Set(synced.map((s) => s.key).filter((k) => !existingKeys.has(k))).size;

    setScoringItems((prev) => {
      const prevKeys = new Set(prev.map((item) => item.key));
      const merged = prev.map((item) => {
        const hit = synced.find((s) => s.key === item.key);
        if (!hit || (item.item_type || "pytest") !== "pytest") return item;
        return {
          ...item,
          inputs: hit.inputs ?? item.inputs,
          outputs: hit.outputs ?? item.outputs,
          comparison_mode: hit.comparison_mode ?? item.comparison_mode ?? "normalized",
          tolerance: hit.tolerance ?? item.tolerance,
        };
      });
      const added: RubricItem[] = [];
      synced.forEach((s) => {
        if (prevKeys.has(s.key) || added.some((a) => a.key === s.key)) return;
        added.push({
          id: `marker_${s.key}_${Math.random().toString(36).slice(2, 7)}`,
          key: s.key,
          label: `${s.key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())} Test`,
          points: 10,
          extra_credit: false,
          item_type: "pytest",
          pytest_marker: pytestMarkerForKey(s.key),
          rubric_group_key: null,
          inputs: s.inputs ?? undefined,
          outputs: s.outputs ?? undefined,
          comparison_mode: s.comparison_mode ?? "normalized",
          tolerance: s.tolerance ?? null,
        });
      });
      return [...merged, ...added];
    });
    markDirty();
    return addedCount;
  };
  // Code editor modal mutators
  const openCodeEditor = async (key: string, type: string, filename: string, initialText?: string) => {
    setErrorMessage(null);
    setEditArtifactKey(key);
    setEditArtifactType(type);
    setEditArtifactFilename(filename);
    setEditCodeText("");
    setIsCodeModalOpen(true);
    if (initialText !== undefined) {
      setEditCodeText(initialText);
      setIsLoadingCode(false);
      return;
    }
    setIsLoadingCode(true);

    try {
      const text = await apiClient.getText(
        `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts/${key}`
      );
      setEditCodeText(text);
    } catch (err: unknown) {
      setIsCodeModalOpen(false);
      setErrorMessage(err instanceof Error ? err.message : "Failed to fetch artifact code.");
    } finally {
      setIsLoadingCode(false);
    }
  };

  const saveCodeChanges = async () => {
    if (!editArtifactKey) return;
    setIsSavingCode(true);
    setErrorMessage(null);
    try {
      const file = new File([editCodeText], editArtifactFilename, { type: "text/plain" });
      const formData = new FormData();
      formData.append("file", file);
      formData.append("artifact_key", editArtifactKey);
      formData.append("artifact_type", editArtifactType);

      await apiClient.postForm(`/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`, formData);
      if (editArtifactType === "pytest_file" || editArtifactType === "test_file" || editArtifactKey === "assignment_tests") {
        setTestSuiteCode(editCodeText);
        setTestSuiteDirty(false);
      }
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
    if (loadingTestSuiteCode) return;
    setSaving(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      // pytest suites are pytest_file; gtest/jsdom suites are test_file. io has no suite file.
      const suiteType: ArtifactType = testFramework === "pytest" ? "pytest_file" : "test_file";
      const hasSuiteFile = testFramework !== "io";

      const savedArtifacts = [...artifacts];
      const suiteArtifact = artifacts.find((artifact) => isCompatibleSuite(artifact, testFramework));
      if (hasSuiteFile && (testSuiteDirty || !suiteArtifact)) {
        const occupied = new Set([
          ...artifacts.map((artifact) => artifact.artifact_key),
          ...Object.keys(loadedConfigRef.current?.artifacts || {}),
        ]);
        const baseKey = occupied.has("assignment_tests") ? `assignment_tests_${testFramework}` : "assignment_tests";
        let availableKey = baseKey;
        for (let suffix = 2; occupied.has(availableKey); suffix++) {
          availableKey = `${baseKey}_${suffix}`;
        }
        const artifactKey = suiteArtifact?.artifact_key || availableKey;
        const filename = suiteArtifact?.display_filename || defaultSuiteFilename(testFramework);
        const file = new File([testSuiteCode], filename, { type: "text/plain" });
        const formData = new FormData();
        formData.append("file", file);
        formData.append("artifact_key", artifactKey);
        formData.append("artifact_type", suiteType);
        await apiClient.postForm(
          `/staff/courses/${courseId}/assignments/${assignmentId}/artifacts`,
          formData
        );
        if (!suiteArtifact) {
          savedArtifacts.push({
            artifact_key: artifactKey, artifact_type: suiteType, display_filename: filename, size_bytes: file.size,
          });
          setArtifacts(savedArtifacts);
        }
        setTestSuiteDirty(false);
      } else if (testSuiteDirty) {
        setTestSuiteDirty(false);
      }

      // Build artifacts dict for config reference check
      const knownTypes: ArtifactType[] = ["pytest_file", "test_file", "model_solution", "support_file"];
      const artifactsDict: Record<string, { type: ArtifactType; display_filename?: string }> = {};
      savedArtifacts.forEach((art) => {
        if (isSuiteArtifact(art) && !isCompatibleSuite(art, testFramework)) return;
        const artType = (knownTypes as string[]).includes(art.artifact_type)
          ? (art.artifact_type as ArtifactType)
          : "support_file";
        artifactsDict[art.artifact_key] = {
          type: artType,
          display_filename: art.display_filename || undefined,
        };
      });

      const derivedRubricGroups = rubricGroups.length > 0
        ? rubricGroups
        : scoringItems.map((item) => ({ key: item.key, label: item.label }));

      const trimmedDescription = description.trim();
      const finalDescription = trimmedDescription === "" ? null : trimmedDescription;

      const config: AssignmentConfigV1 = {
        ...loadedConfigRef.current,
        test_framework: testFramework,
        description: finalDescription,
        bundle: {
          ...loadedConfigRef.current?.bundle,
          entrypoint,
          file_requirements: fileRequirements,
          language,
        },
        artifacts: artifactsDict,
        scoring_items: scoringItems,
        rubric_groups: derivedRubricGroups,
        dependencies,
        concepts: {
          ...loadedConfigRef.current?.concepts,
          denylist: conceptDenylist,
        },
      };


      await apiClient.put(`/staff/courses/${courseId}/assignments/${assignmentId}/setup`, {
        title,
        canvas_ref: canvasRef.trim() || null,
        description: finalDescription,
        sandbox_enabled: sandboxEnabled,
        module_id: moduleId,
        language,
        config,
      });

      setSaveSuccess(true);
      setSuccessMessage(null);
      pendingBaselineRef.current = true;
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
        canvasRef,
        setCanvasRef,
        description,
        setDescription,
        moduleId,
        setModuleId,
        sandboxEnabled,
        setSandboxEnabled,
        language,
        setLanguage,
        testFramework,
        setTestFramework,

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
        syncTestsFromSource,


        conceptDenylist,
        toggleConceptDenylist,
        inheritedConcepts,
        effectiveConcepts,


        courseDefaultConcepts,
        moduleConcepts,
        conceptMeta,
        courseModules,
        dependencies,

        artifacts,
        setArtifacts,
        refreshArtifacts,
        testSuiteCode,
        updateTestSuiteCode,
        loadingTestSuiteCode,
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
        handleDiscard,
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
