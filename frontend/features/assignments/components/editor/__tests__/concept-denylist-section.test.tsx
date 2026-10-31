import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConceptDenylistSection } from "../concept-denylist-section";
import {
  AssignmentEditorContext,
  AssignmentEditorContextType,
} from "../assignment-editor-context";

function createMockContext(
  overrides?: Partial<AssignmentEditorContextType>
): AssignmentEditorContextType {
  return {
    courseId: "cs1410",
    assignmentId: "lab1",
    loading: false,
    saving: false,
    dirty: false,
    saveSuccess: false,
    errorMessage: null,
    successMessage: null,
    setErrorMessage: vi.fn(),
    setSuccessMessage: vi.fn(),
    markDirty: vi.fn(),
    handleDiscard: vi.fn(),

    title: "Lab 1",
    setTitle: vi.fn(),
    description: "",
    setDescription: vi.fn(),
    moduleId: 1,
    setModuleId: vi.fn(),
    sandboxEnabled: true,
    setSandboxEnabled: vi.fn(),
    language: "python",
    setLanguage: vi.fn(),

    entrypoint: "main.py",
    setEntrypoint: vi.fn(),
    fileRequirements: [],
    addFileRequirement: vi.fn(),
    removeFileRequirement: vi.fn(),
    updateFileRequirement: vi.fn(),
    updateFileRequirementPath: vi.fn(),
    addFileRequirementPath: vi.fn(),
    removeFileRequirementPath: vi.fn(),
    toggleFileRequirementGlob: vi.fn(),

    scoringItems: [],
    addScoringItem: vi.fn(),
    removeScoringItem: vi.fn(),
    updateScoringItemField: vi.fn(),
    rubricGroups: [],
    syncMarkersFromTestSuite: vi.fn(),

    conceptDenylist: ["recursion"],
    toggleConceptDenylist: vi.fn(),
    inheritedConcepts: ["loops", "recursion"],
    effectiveConcepts: ["loops"],
    courseDefaultConcepts: ["loops"],
    moduleConcepts: ["recursion"],
    conceptMeta: {
      loops: {
        key: "loops",
        title: "Loops & Iteration",
        syntax_patterns: ["For", "While"],
        nodes: ["For", "While"],
      },
      recursion: {
        key: "recursion",
        title: "Recursion",
        syntax_patterns: ["FunctionDef"],
        nodes: ["FunctionDef"],
      },
    },
    courseModules: [{ id: 1, name: "Module 1" }],
    dependencies: [],

    artifacts: [],
    setArtifacts: vi.fn(),
    refreshArtifacts: vi.fn(),
    testSuiteCode: "",
    updateTestSuiteCode: vi.fn(),
    loadingTestSuiteCode: false,
    isCodeModalOpen: false,
    setIsCodeModalOpen: vi.fn(),
    editArtifactKey: null,
    editArtifactFilename: "",
    editCodeText: "",
    setEditCodeText: vi.fn(),
    isLoadingCode: false,
    isSavingCode: false,
    openCodeEditor: vi.fn(),
    saveCodeChanges: vi.fn(),

    handleSave: vi.fn(),
    handleDelete: vi.fn(),
    handleCopyStudentLink: vi.fn(),
    copiedLink: false,
    ...overrides,
  };
}

describe("ConceptDenylistSection", () => {
  it("renders empty state message when no module is assigned", () => {
    const mockCtx = createMockContext({
      moduleId: null,
      inheritedConcepts: [],
    });

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ConceptDenylistSection />
      </AssignmentEditorContext.Provider>
    );

    expect(
      screen.getByText(/Assign a module under General & Files to inherit concepts/i)
    ).toBeDefined();
  });

  it("renders inherited concepts with active and disabled states", () => {
    const mockCtx = createMockContext();

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ConceptDenylistSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByText("Loops & Iteration")).toBeDefined();
    expect(screen.getByText("Course")).toBeDefined();

    expect(screen.getByText("Recursion")).toBeDefined();
    expect(screen.getByText("Disabled")).toBeDefined();
  });

  it("calls toggleConceptDenylist when a concept button is clicked", () => {
    const mockCtx = createMockContext();

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ConceptDenylistSection />
      </AssignmentEditorContext.Provider>
    );

    const loopsBtn = screen.getByRole("button", { name: /Loops & Iteration/i });
    fireEvent.click(loopsBtn);

    expect(mockCtx.toggleConceptDenylist).toHaveBeenCalledWith("loops");
  });
});
