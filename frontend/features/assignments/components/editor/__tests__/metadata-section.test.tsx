import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MetadataSection } from "../metadata-section";
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

    title: "Lab 1: Control Flow",
    setTitle: vi.fn(),
    description: "Write functions to solve problems.",
    setDescription: vi.fn(),
    moduleId: 1,
    setModuleId: vi.fn(),
    sandboxEnabled: true,
    setSandboxEnabled: vi.fn(),
    language: "python",
    setLanguage: vi.fn(),

    entrypoint: "solution.py",
    setEntrypoint: vi.fn(),
    fileRequirements: [
      { paths: ["solution.py", "main.py"] },
    ],
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

    conceptDenylist: [],
    toggleConceptDenylist: vi.fn(),
    inheritedConcepts: [],
    effectiveConcepts: [],
    courseDefaultConcepts: [],
    moduleConcepts: [],
    conceptMeta: {},
    courseModules: [
      { id: 1, name: "Module 1: Basics" },
      { id: 2, name: "Module 2: OOP" },
    ],
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

describe("MetadataSection", () => {
  it("renders title input and triggers setTitle and markDirty on change", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <MetadataSection />
      </AssignmentEditorContext.Provider>
    );

    const titleInput = screen.getByDisplayValue("Lab 1: Control Flow");
    fireEvent.change(titleInput, { target: { value: "Lab 1: Updated Title" } });

    expect(mockCtx.setTitle).toHaveBeenCalledWith("Lab 1: Updated Title");
    expect(mockCtx.markDirty).toHaveBeenCalled();
  });

  it("renders description textarea and triggers setDescription on change", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <MetadataSection />
      </AssignmentEditorContext.Provider>
    );

    const descInput = screen.getByDisplayValue("Write functions to solve problems.");
    fireEvent.change(descInput, { target: { value: "Updated description instructions." } });

    expect(mockCtx.setDescription).toHaveBeenCalledWith("Updated description instructions.");
    expect(mockCtx.markDirty).toHaveBeenCalled();
  });

  it("toggles sandboxEnabled checkbox and marks dirty", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <MetadataSection />
      </AssignmentEditorContext.Provider>
    );

    const sandboxCheckbox = screen.getByLabelText(/Enable Student Sandbox Access/i);
    fireEvent.click(sandboxCheckbox);

    expect(mockCtx.setSandboxEnabled).toHaveBeenCalledWith(false);
    expect(mockCtx.markDirty).toHaveBeenCalled();
  });

  it("renders file requirements and triggers addFileRequirement", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <MetadataSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByDisplayValue("solution.py")).toBeDefined();
    expect(screen.getByDisplayValue("main.py")).toBeDefined();

    const addFileBtn = screen.getByRole("button", { name: /Add Required File/i });
    fireEvent.click(addFileBtn);

    expect(mockCtx.addFileRequirement).toHaveBeenCalled();
  });

  it("triggers removeFileRequirement when delete icon button is clicked", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <MetadataSection />
      </AssignmentEditorContext.Provider>
    );

    const removeBtn = screen.getByRole("button", { name: /Remove file requirement/i });
    fireEvent.click(removeBtn);

    expect(mockCtx.removeFileRequirement).toHaveBeenCalledWith(0);
  });

  it("triggers toggleFileRequirementGlob when glob checkbox is clicked", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <MetadataSection />
      </AssignmentEditorContext.Provider>
    );

    const globCheckbox = screen.getByLabelText(/Treat as glob pattern/i);
    fireEvent.click(globCheckbox);

    expect(mockCtx.toggleFileRequirementGlob).toHaveBeenCalledWith(0, true);
  });

  it("triggers addFileRequirementPath when Add Alternate File Name is clicked", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <MetadataSection />
      </AssignmentEditorContext.Provider>
    );

    const addAltBtn = screen.getByRole("button", { name: /Add Alternate File Name/i });
    fireEvent.click(addAltBtn);

    expect(mockCtx.addFileRequirementPath).toHaveBeenCalledWith(0);
  });
});
