import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ScoringRulesSection } from "../scoring-rules-section";
import {
  AssignmentEditorContext,
  AssignmentEditorContextType,
} from "../assignment-editor-context";

vi.mock("@/components/monaco-editor", () => ({
  default: ({ value, onChange }: { value: string; onChange?: (val: string) => void }) => (
    <textarea
      data-testid="monaco-mock"
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
    />
  ),
}));

vi.mock("../ai-test-assistant-dialog", () => ({
  AITestAssistantDialog: () => <div data-testid="ai-assistant-dialog-mock" />,
}));

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
    description: "Lab description",
    setDescription: vi.fn(),
    moduleId: 1,
    setModuleId: vi.fn(),
    sandboxEnabled: true,
    setSandboxEnabled: vi.fn(),
    language: "python",
    setLanguage: vi.fn(),

    entrypoint: "main.py",
    setEntrypoint: vi.fn(),
    fileRequirements: [{ paths: ["main.py"] }],
    addFileRequirement: vi.fn(),
    removeFileRequirement: vi.fn(),
    updateFileRequirement: vi.fn(),
    updateFileRequirementPath: vi.fn(),
    addFileRequirementPath: vi.fn(),
    removeFileRequirementPath: vi.fn(),
    toggleFileRequirementGlob: vi.fn(),

    scoringItems: [
      {
        key: "part1_files",
        label: "Required files exist",
        points: 10,
        extra_credit: false,
        item_type: "pytest",
        pytest_marker: "ag_part1_files",
        rubric_group_key: null,
      },
      {
        key: "bonus_challenge",
        label: "Bonus challenge",
        points: 5,
        extra_credit: true,
        item_type: "pytest",
        pytest_marker: "ag_bonus_challenge",
        rubric_group_key: null,
      },
    ],
    addScoringItem: vi.fn(),
    removeScoringItem: vi.fn(),
    updateScoringItemField: vi.fn(),
    rubricGroups: [],
    syncMarkersFromTestSuite: vi.fn(),

    conceptDenylist: [],
    toggleConceptDenylist: vi.fn(),
    inheritedConcepts: ["variables", "loops"],
    effectiveConcepts: ["variables", "loops"],
    courseDefaultConcepts: ["variables"],
    moduleConcepts: ["loops"],
    conceptMeta: {
      variables: { key: "variables", title: "Variables", syntax_patterns: ["Assign"], nodes: ["Assign"] },
      loops: { key: "loops", title: "Loops", syntax_patterns: ["For", "While"], nodes: ["For", "While"] },
    },
    courseModules: [{ id: 1, name: "Module 1" }],
    dependencies: [],

    artifacts: [],
    setArtifacts: vi.fn(),
    refreshArtifacts: vi.fn(),
    testSuiteCode: `
import pytest

@pytest.mark.ag_part1_files
def test_files():
    pass

@pytest.mark.ag_bonus_challenge
def test_bonus():
    pass
`,
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

describe("ScoringRulesSection", () => {
  it("renders point totals separating base and extra credit points", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByText(/10 pts · \+5 extra credit/)).toBeDefined();
  });

  it("renders rubric item labels and allows updating point values", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByDisplayValue("Required files exist")).toBeDefined();
    expect(screen.getByDisplayValue("Bonus challenge")).toBeDefined();
  });

  it("triggers addScoringItem when clicking Add button in Autograded criteria header", () => {
    const mockCtx = createMockContext();
    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    const addButtons = screen.getAllByRole("button", { name: /add/i });
    fireEvent.click(addButtons[0]);
    expect(mockCtx.addScoringItem).toHaveBeenCalledWith("pytest");
  });

  it("detects and displays warnings when tests.py contains markers not in rubric", () => {
    const mockCtx = createMockContext({
      testSuiteCode: `
@pytest.mark.ag_part1_files
def test_files():
    pass

@pytest.mark.ag_untracked_test
def test_untracked():
    pass
`,
    });

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByText(/in tests\.py not in the rubric/i)).toBeDefined();
    expect(screen.getByText(/\(ag_untracked_test\)/i)).toBeDefined();
  });

  it("detects and displays warnings when rubric items have no matching marker in tests.py", () => {
    const mockCtx = createMockContext({
      testSuiteCode: `
@pytest.mark.ag_part1_files
def test_files():
    pass
`,
    });

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(
      screen.getByText(/rubric key missing from tests\.py/i)
    ).toBeDefined();
    expect(screen.getByText(/\(ag_bonus_challenge\)/i)).toBeDefined();
  });

  it("calls syncMarkersFromTestSuite when Sync from tests button is clicked", () => {
    const mockCtx = createMockContext();
    vi.mocked(mockCtx.syncMarkersFromTestSuite).mockReturnValue(1);

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    const syncBtn = screen.getByRole("button", { name: /sync from tests/i });
    fireEvent.click(syncBtn);

    expect(mockCtx.syncMarkersFromTestSuite).toHaveBeenCalled();
    expect(mockCtx.setSuccessMessage).toHaveBeenCalledWith(
      "Synced 1 new pytest marker(s) into the rubric."
    );
  });
});
