import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
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
    canvasRef: "",
    setCanvasRef: vi.fn(),
    description: "Lab description",
    setDescription: vi.fn(),
    moduleId: 1,
    setModuleId: vi.fn(),
    sandboxEnabled: true,
    setSandboxEnabled: vi.fn(),
    language: "python",
    setLanguage: vi.fn(),
    testFramework: "pytest",
    setTestFramework: vi.fn(),

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
    syncTestsFromSource: vi.fn(),

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

  it("labels the automated item section as Automated tests", () => {
    render(
      <AssignmentEditorContext.Provider value={createMockContext()}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByText("Automated tests")).toBeDefined();
    expect(screen.getByText("tests.py")).toBeDefined();
  });

  it("calls syncTestsFromSource when Sync from tests button is clicked", async () => {
    const mockCtx = createMockContext();
    vi.mocked(mockCtx.syncTestsFromSource).mockResolvedValue(1);

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    fireEvent.click(screen.getByRole("button", { name: /sync from tests/i }));

    expect(mockCtx.syncTestsFromSource).toHaveBeenCalledWith(mockCtx.testSuiteCode);
    await waitFor(() =>
      expect(mockCtx.setSuccessMessage).toHaveBeenCalledWith(
        "Synced 1 new pytest marker(s) into the rubric."
      )
    );
  });

  it("does not report success when the sync fails", async () => {
    const mockCtx = createMockContext();
    vi.mocked(mockCtx.syncTestsFromSource).mockResolvedValue(null);

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    fireEvent.click(screen.getByRole("button", { name: /sync from tests/i }));
    await waitFor(() => expect(mockCtx.syncTestsFromSource).toHaveBeenCalled());
    expect(mockCtx.setSuccessMessage).not.toHaveBeenCalled();
  });

  it("hides Python helpers, AI assistant and sync for non-Python languages", () => {
    render(
      <AssignmentEditorContext.Provider
        value={createMockContext({ language: "cpp", testFramework: "gtest", testSuiteCode: "TEST(A, ag_main) {}" })}
      >
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByText("tests.cpp")).toBeDefined();
    expect(screen.queryByRole("button", { name: /view python helpers/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /tests with ai/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /sync from tests/i })).toBeNull();
    expect(screen.queryByTestId("ai-assistant-dialog-mock")).toBeNull();
  });

  it.each([
    ["gtest", "cpp", "tests.cpp"],
    ["jsdom", "web", "tests.cjs"],
  ] as const)("hides comparison controls for the %s framework", (framework, language, filename) => {
    render(
      <AssignmentEditorContext.Provider value={createMockContext({ language, testFramework: framework })}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByText(filename)).toBeDefined();
    expect(screen.queryAllByLabelText(/comparison mode/i)).toHaveLength(0);
  });

  it("edits I/O case rows and hides the suite editor for the io framework", () => {
    const mockCtx = createMockContext({
      language: "c",
      testFramework: "io",
      scoringItems: [
        {
          key: "hello",
          label: "Prints hello",
          points: 10,
          extra_credit: false,
          item_type: "pytest",
          pytest_marker: null,
          rubric_group_key: null,
          inputs: ["Ada"],
          outputs: ["Hello Ada"],
          comparison_mode: "normalized",
        },
      ],
    });

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.queryByTestId("monaco-mock")).toBeNull();
    expect(screen.getAllByLabelText(/comparison mode/i)).toHaveLength(1);

    fireEvent.change(screen.getByLabelText("Case 1 expected output"), { target: { value: "Hi Ada" } });
    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith("hello", "inputs", ["Ada"]);
    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith("hello", "outputs", ["Hi Ada"]);

    fireEvent.click(screen.getByRole("button", { name: /add case/i }));
    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith("hello", "inputs", ["Ada", ""]);
    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith("hello", "outputs", ["Hello Ada", ""]);
  });
  it("renders comparison mode select and handles mode changes", () => {
    const mockCtx = createMockContext();

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    const modeSelects = screen.getAllByLabelText(/comparison mode/i);
    expect(modeSelects.length).toBe(2);

    fireEvent.change(modeSelects[0], { target: { value: "exact" } });
    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith(
      "part1_files",
      "comparison_mode",
      "exact"
    );
  });

  it("renders tolerance input when numeric_tolerance mode is selected", () => {
    const mockCtx = createMockContext({
      scoringItems: [
        {
          key: "float_test",
          label: "Float Test",
          points: 10,
          extra_credit: false,
          item_type: "pytest",
          pytest_marker: "ag_float_test",
          rubric_group_key: null,
          comparison_mode: "numeric_tolerance",
          tolerance: 0.001,
        },
      ],
    });

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    const tolInput = screen.getByLabelText(/tolerance/i);
    expect(tolInput).toBeDefined();
    expect((tolInput as HTMLInputElement).value).toBe("0.001");

    fireEvent.change(tolInput, { target: { value: "0.0005" } });
    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith(
      "float_test",
      "tolerance",
      0.0005
    );
  });

  it("renders comment snippets and triggers updateScoringItemField on add and remove", () => {
    const mockCtx = createMockContext({
      scoringItems: [
        {
          key: "code_style",
          label: "Code Style",
          points: 10,
          extra_credit: false,
          item_type: "manual",
          pytest_marker: null,
          rubric_group_key: null,
          comment_templates: ["Missing docstrings", "PEP 8 naming"],
        },
      ],
    });

    render(
      <AssignmentEditorContext.Provider value={mockCtx}>
        <ScoringRulesSection />
      </AssignmentEditorContext.Provider>
    );

    expect(screen.getByText("Missing docstrings")).toBeDefined();
    expect(screen.getByText("PEP 8 naming")).toBeDefined();

    // Remove first snippet
    const removeBtn = screen.getByLabelText(/remove snippet "missing docstrings"/i);
    fireEvent.click(removeBtn);
    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith(
      "code_style",
      "comment_templates",
      ["PEP 8 naming"]
    );

    // Add a new snippet
    const addInput = screen.getByPlaceholderText(/add snippet for Code Style/i);
    fireEvent.change(addInput, { target: { value: "Refactor nested loops" } });
    const addBtn = screen.getByRole("button", { name: /add snippet/i });
    fireEvent.click(addBtn);

    expect(mockCtx.updateScoringItemField).toHaveBeenCalledWith(
      "code_style",
      "comment_templates",
      ["Missing docstrings", "PEP 8 naming", "Refactor nested loops"]
    );
  });
});
