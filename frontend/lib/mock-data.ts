import type {
  Assignment,
  AssignmentsResponse,
  ConceptMetadata,
  SandboxAiFeedbackResponse,
  SandboxRunResultResponse,
  StaffAssignmentSetup,
} from "@/features/assignments/types";
import type {
  CourseAdminDetail,
  SandboxCoursesResponse,
  StaffCoursesResponse,
} from "@/features/courses/types";
import type {
  MonitoringStats,
  SectionAdminDetail,
  StaffAccessRecord,
} from "@/features/courses/api";
import type {
  RunDetailsResponse,
  RunSummary,
  StudentFile,
} from "@/features/runs/types";
import type {
  AuditRecord,
  AuditStatsResponse,
  AuditVerificationResponse,
} from "@/features/audit/types";
import mockCatalog from "./mock-catalog.json";

export { mockCatalog };

export const MOCK_SANDBOX_COURSES: SandboxCoursesResponse = {
  courses: [
    {
      id: "cs1400",
      title: "Fundamentals of Programming",
      term: "Fall 2026",
      sandbox_enabled_assignments: mockCatalog.cs1400.assignments.length,
    },
    {
      id: "cs1410",
      title: "Object-Oriented Programming",
      term: "Fall 2026",
      sandbox_enabled_assignments: mockCatalog.cs1410.assignments.length,
    },
  ],
};

export const MOCK_STAFF_COURSES: StaffCoursesResponse = {
  courses: [
    {
      id: "cs1400",
      title: "Fundamentals of Programming",
      term: "Fall 2026",
      assignment_count: mockCatalog.cs1400.assignments.length,
    },
    {
      id: "cs1410",
      title: "Object-Oriented Programming",
      term: "Fall 2026",
      assignment_count: mockCatalog.cs1410.assignments.length,
    },
  ],
};

export const MOCK_ADMIN_COURSES: CourseAdminDetail[] = [
  {
    id: 1,
    code: "CS 1410",
    title: "Object-Oriented Programming",
    term: "Fall 2026",
    is_active: true,
    instructor_id: 1,
    instructor_email: "dev.staff@uvu.edu",
    ia_id: 2,
    ia_email: "dev.ia@uvu.edu",
    default_concepts: [
      "variables",
      "conditionals",
      "functions",
      "classes",
      "inheritance",
    ],
    section_count: 3,
    assignment_count: mockCatalog.cs1410.assignments.length,
  },
  {
    id: 2,
    code: "CS 1400",
    title: "Fundamentals of Programming",
    term: "Fall 2026",
    is_active: true,
    instructor_id: 1,
    instructor_email: "dev.staff@uvu.edu",
    ia_id: null,
    ia_email: null,
    default_concepts: ["variables", "conditionals", "functions"],
    section_count: 1,
    assignment_count: mockCatalog.cs1400.assignments.length,
  },
];

export const MOCK_ASSIGNMENTS_CS1400: AssignmentsResponse = {
  course_id: "cs1400",
  assignments: mockCatalog.cs1400.assignments.map((a) => ({
    id: a.id,
    course_id: "cs1400",
    title: a.title,
    description: a.summary,
    sandbox_enabled: true,
    language: "python",
    max_score: 100,
    upload_quota: {
      limit: 10,
      window_seconds: 3600,
      remaining: 10,
      reset_at: new Date(Date.now() + 3600000).toISOString(),
    },
    module_name: a.module_name,
  })),
};

export const MOCK_ASSIGNMENTS_CS1410: AssignmentsResponse = {
  course_id: "cs1410",
  assignments: mockCatalog.cs1410.assignments.map((a) => ({
    id: a.id,
    course_id: "cs1410",
    title: a.title,
    description: a.summary,
    sandbox_enabled: true,
    language: "python",
    max_score: 100,
    upload_quota: {
      limit: 10,
      window_seconds: 3600,
      remaining: 10,
      reset_at: new Date(Date.now() + 3600000).toISOString(),
    },
    module_name: a.module_name,
  })),
};

export const MOCK_ASSIGNMENT_DETAILS_LAB1: Assignment = {
  id: "lab1",
  course_id: "1",
  title: "Lab 1 - Image Processing",
  description:
    "## Lab 1: Image Processing\n\nIn this lab, you will implement image filtering operations using 2D pixel arrays.\n\n### Objectives\n- Parse PPM image headers and body lines\n- Implement `invert_pixels(pixels)`\n- Implement `grayscale(pixels)`\n- Comply with structural memory bounds",
  sandbox_enabled: true,
  language: "python",
  max_score: 100,
  upload_quota: {
    limit: 10,
    window_seconds: 3600,
    remaining: 10,
    reset_at: new Date(Date.now() + 3600000).toISOString(),
  },
  module_name: "Module 1",
  accepted_bundle_types: ["zip", "py"],
  max_upload_bytes: 5242880,
  constraints: [
    { label: "Memory Limit", value: "256 MB" },
    { label: "Timeout", value: "30s" },
    { label: "Execution Sandbox", value: "Kata microVM" },
  ],
  allowed_concepts: ["variables", "conditionals", "functions", "lists"],
  rubric: [
    {
      id: "1",
      key: "test_invert",
      label: "Invert Filter",
      points: 40,
      extra_credit: false,
      pytest_marker: "ag_key('test_invert')",
      item_type: "pytest",
      rubric_group_key: "functional",
    },
    {
      id: "2",
      key: "test_grayscale",
      label: "Grayscale Filter",
      points: 40,
      extra_credit: false,
      pytest_marker: "ag_key('test_grayscale')",
      item_type: "pytest",
      rubric_group_key: "functional",
    },
    {
      id: "3",
      key: "test_ast",
      label: "AST Safety Check",
      points: 20,
      extra_credit: false,
      pytest_marker: "ag_key('test_ast')",
      item_type: "pytest",
      rubric_group_key: "style",
    },
  ],
  rubric_groups: [
    { key: "functional", label: "Functional Requirements" },
    { key: "style", label: "Code Structure & Policy" },
  ],
  completion_requirements: [],
  config: {
    description: "## Lab 1: Image Processing\n\nImplement image filtering operations.",
    bundle: {
      entrypoint: "image_processor.py",
      file_requirements: [
        {
          paths: ["image_processor.py"],
        },
      ],
    },
    artifacts: {
      test_solution: {
        type: "pytest_file",
        display_filename: "test_image_processor.py",
      },
    },
    scoring_items: [
      {
        key: "test_invert",
        label: "Invert Filter",
        points: 40,
        extra_credit: false,
        pytest_marker: "ag_key('test_invert')",
        item_type: "pytest",
        rubric_group_key: "functional",
      },
      {
        key: "test_grayscale",
        label: "Grayscale Filter",
        points: 40,
        extra_credit: false,
        pytest_marker: "ag_key('test_grayscale')",
        item_type: "pytest",
        rubric_group_key: "functional",
      },
      {
        key: "test_ast",
        label: "AST Safety Check",
        points: 20,
        extra_credit: false,
        pytest_marker: "ag_key('test_ast')",
        item_type: "pytest",
        rubric_group_key: "style",
      },
    ],
  },
};

export const MOCK_ASSIGNMENT_DETAILS_DS1: Assignment = {
  id: "ds1",
  course_id: "cs1410",
  title: "Dessert Shop 1: Inheritance Superclass",
  description:
    mockCatalog.cs1410.assignments.find((a) => a.id === "ds1")?.description ||
    "## Dessert Shop 1: Inheritance Superclass\n\nBuild the DessertItem superclass and derived subclasses.",
  sandbox_enabled: true,
  language: "python",
  max_score: 100,
  upload_quota: {
    limit: 10,
    window_seconds: 3600,
    remaining: 10,
    reset_at: new Date(Date.now() + 3600000).toISOString(),
  },
  module_name: "Module 3: Inheritance, Polymorphism, and Properties",
  accepted_bundle_types: ["zip", "py"],
  max_upload_bytes: 5242880,
  constraints: [
    { label: "Memory Limit", value: "256 MB" },
    { label: "Timeout", value: "30s" },
    { label: "Execution Sandbox", value: "Kata microVM" },
  ],
  allowed_concepts: [
    "image-processing",
    "classes",
    "type-hints",
    "inheritance",
    "properties",
    "operator-overloading",
    "exceptions",
  ],
  rubric: [
    {
      id: "1",
      key: "test_dessert_item",
      label: "DessertItem Superclass",
      points: 40,
      extra_credit: false,
      pytest_marker: "ag_key('test_dessert_item')",
      item_type: "pytest",
      rubric_group_key: "core",
    },
    {
      id: "2",
      key: "test_subclasses",
      label: "Subclasses (Candy, Cookie, IceCream, Sundae)",
      points: 40,
      extra_credit: false,
      pytest_marker: "ag_key('test_subclasses')",
      item_type: "pytest",
      rubric_group_key: "core",
    },
    {
      id: "3",
      key: "test_ast",
      label: "AST Safety Check",
      points: 20,
      extra_credit: false,
      pytest_marker: "ag_key('test_ast')",
      item_type: "pytest",
      rubric_group_key: "style",
    },
  ],
  rubric_groups: [
    { key: "core", label: "Core Requirements" },
    { key: "style", label: "Code Structure & Policy" },
  ],
  completion_requirements: [],
  config: {
    description: "Build the DessertItem superclass and derived subclasses.",
    bundle: {
      entrypoint: "dessert.py",
      file_requirements: [{ paths: ["dessert.py"] }],
    },
    artifacts: {
      test_solution: {
        type: "pytest_file",
        display_filename: "test_dessert.py",
      },
    },
    scoring_items: [
      {
        key: "test_dessert_item",
        label: "DessertItem Superclass",
        points: 40,
        extra_credit: false,
        pytest_marker: "ag_key('test_dessert_item')",
        item_type: "pytest",
        rubric_group_key: "core",
      },
      {
        key: "test_subclasses",
        label: "Subclasses (Candy, Cookie, IceCream, Sundae)",
        points: 40,
        extra_credit: false,
        pytest_marker: "ag_key('test_subclasses')",
        item_type: "pytest",
        rubric_group_key: "core",
      },
      {
        key: "test_ast",
        label: "AST Safety Check",
        points: 20,
        extra_credit: false,
        pytest_marker: "ag_key('test_ast')",
        item_type: "pytest",
        rubric_group_key: "style",
      },
    ],
  },
};

export function getMockAssignment(courseId: string, slug: string): Assignment {
  if (slug === "lab1" && courseId !== "cs1400" && courseId !== "2") {
    return MOCK_ASSIGNMENT_DETAILS_LAB1;
  }
  if (slug === "ds1" && courseId !== "cs1400" && courseId !== "2") {
    return MOCK_ASSIGNMENT_DETAILS_DS1;
  }

  const is1400 = courseId === "cs1400" || courseId === "2" || slug.startsWith("m");
  const courseKey = is1400 ? "cs1400" : "cs1410";
  const catalogList = mockCatalog[courseKey].assignments;
  const found =
    catalogList.find((a) => a.slug === slug || a.id === slug) ||
    catalogList[0];

  return {
    id: found.id,
    course_id: courseKey,
    title: found.title,
    description: found.description || found.summary,
    sandbox_enabled: true,
    language: "python",
    max_score: 100,
    upload_quota: {
      limit: 10,
      window_seconds: 3600,
      remaining: 10,
      reset_at: new Date(Date.now() + 3600000).toISOString(),
    },
    module_name: found.module_name,
    accepted_bundle_types: ["zip", "py"],
    max_upload_bytes: 5242880,
    constraints: [
      { label: "Memory Limit", value: "256 MB" },
      { label: "Timeout", value: "30s" },
      { label: "Execution Sandbox", value: "Kata microVM" },
    ],
    allowed_concepts:
      found.concepts && found.concepts.length > 0
        ? found.concepts
        : ["variables", "conditionals", "functions"],
    rubric: [
      {
        id: "1",
        key: "test_main",
        label: "Functional Implementation",
        points: 80,
        extra_credit: false,
        pytest_marker: "ag_key('test_main')",
        item_type: "pytest",
        rubric_group_key: "functional",
      },
      {
        id: "2",
        key: "test_ast",
        label: "AST Safety Check",
        points: 20,
        extra_credit: false,
        pytest_marker: "ag_key('test_ast')",
        item_type: "pytest",
        rubric_group_key: "style",
      },
    ],
    rubric_groups: [
      { key: "functional", label: "Functional Requirements" },
      { key: "style", label: "Code Structure & Policy" },
    ],
    completion_requirements: [],
    config: {
      description: found.description || found.summary,
      bundle: {
        entrypoint: "main.py",
        file_requirements: [{ paths: ["main.py"] }],
      },
      artifacts: {
        test_solution: {
          type: "pytest_file",
          display_filename: "test_solution.py",
        },
      },
      scoring_items: [
        {
          key: "test_main",
          label: "Functional Implementation",
          points: 80,
          extra_credit: false,
          pytest_marker: "ag_key('test_main')",
          item_type: "pytest",
          rubric_group_key: "functional",
        },
        {
          key: "test_ast",
          label: "AST Safety Check",
          points: 20,
          extra_credit: false,
          pytest_marker: "ag_key('test_ast')",
          item_type: "pytest",
          rubric_group_key: "style",
        },
      ],
    },
  };
}

export function getMockStaffAssignmentSetup(courseId: string, slug: string): StaffAssignmentSetup {
  if (slug === "lab1" && courseId !== "cs1400" && courseId !== "2") {
    return MOCK_STAFF_ASSIGNMENT_SETUP_LAB1;
  }
  const assignment = getMockAssignment(courseId, slug);
  return {
    course_id: assignment.course_id,
    assignment_id: assignment.id,
    title: assignment.title,
    description: assignment.description,
    language: "python",
    sandbox_enabled: true,
    canvas_ref: `canvas-${assignment.id}`,
    base_points: 100,
    extra_credit_points: 0,
    entrypoint_path: assignment.config?.bundle.entrypoint || "main.py",
    scoring_items: assignment.rubric,
    rubric_groups: assignment.rubric_groups,
    completion_requirements: assignment.completion_requirements,
    artifacts: [
      {
        artifact_key: "test_solution",
        artifact_type: "pytest_file",
        display_filename: "test_solution.py",
        size_bytes: 1024,
      },
    ],
    config: assignment.config || {
      description: assignment.description,
      bundle: {
        entrypoint: "main.py",
        file_requirements: [{ paths: ["main.py"] }],
      },
      scoring_items: assignment.rubric,
    },
    effective_allowed_concepts: assignment.allowed_concepts,
  };
}

export const MOCK_CONCEPTS_METADATA: Record<string, ConceptMetadata> = {
  variables: {
    key: "variables",
    title: "Variable Assignment & Expressions",
    syntax_patterns: ["Assign", "AugAssign", "AnnAssign"],
    nodes: ["Assign", "Name"],
  },
  conditionals: {
    key: "conditionals",
    title: "If / Else Branches",
    syntax_patterns: ["If", "IfExp"],
    nodes: ["If"],
  },
  functions: {
    key: "functions",
    title: "Functions & Defs",
    syntax_patterns: ["FunctionDef", "Return", "Call"],
    nodes: ["FunctionDef"],
  },
  classes: {
    key: "classes",
    title: "Object-Oriented Classes",
    syntax_patterns: ["ClassDef"],
    nodes: ["ClassDef"],
  },
  inheritance: {
    key: "inheritance",
    title: "Class Inheritance",
    syntax_patterns: ["ClassDef.bases"],
    nodes: ["ClassDef"],
  },
};

export const MOCK_SANDBOX_RUN_RESULT: SandboxRunResultResponse = {
  run_id: "mock-run-001",
  state: "complete",
  projected_score: 100,
  max_score: 100,
  warnings: [],
  test_summaries: [
    {
      label: "Invert Filter",
      status: "passed",
      points_awarded: 40,
      points_possible: 40,
      message: "Test passed cleanly.",
      group_key: "functional",
    },
    {
      label: "Grayscale Filter",
      status: "passed",
      points_awarded: 40,
      points_possible: 40,
      message: "Test passed cleanly.",
      group_key: "functional",
    },
    {
      label: "AST Safety Check",
      status: "passed",
      points_awarded: 20,
      points_possible: 20,
      message: "All syntax constructs strictly match allowed concepts.",
      group_key: "style",
    },
  ],
  rubric_groups: [
    {
      group_key: "functional",
      label: "Functional Requirements",
      points_earned: 80,
      points_possible: 80,
      items: [
        {
          label: "Invert Filter",
          status: "passed",
          points_awarded: 40,
          points_possible: 40,
          message: "Test passed cleanly.",
        },
        {
          label: "Grayscale Filter",
          status: "passed",
          points_awarded: 40,
          points_possible: 40,
          message: "Test passed cleanly.",
        },
      ],
    },
    {
      group_key: "style",
      label: "Code Structure & Policy",
      points_earned: 20,
      points_possible: 20,
      items: [
        {
          label: "AST Safety Check",
          status: "passed",
          points_awarded: 20,
          points_possible: 20,
          message: "All syntax constructs strictly match allowed concepts.",
        },
      ],
    },
  ],
  sanitized_feedback:
    "============================= test session starts ==============================\n3 passed in 0.42s\nPASSED test_image_processor.py::test_invert\nPASSED test_image_processor.py::test_grayscale\nPASSED test_image_processor.py::test_ast",
  retention_notice:
    "Sandbox runs are non-retained and purged immediately after result retrieval.",
};

export const MOCK_SANDBOX_AI_FEEDBACK: SandboxAiFeedbackResponse = {
  run_id: "mock-run-001",
  ai_feedback:
    "Your implementation of the PPM pixel invert and grayscale filters is mathematically correct and satisfies all unit test assertions. Your code cleanly conforms to the allowed concept subset for Module 1.",
  model: "vllm-cs1410 (gemma-4-12b-qat-lora)",
};

export const MOCK_STAFF_ASSIGNMENT_SETUP_LAB1: StaffAssignmentSetup = {
  course_id: "cs1410",
  assignment_id: "lab1",
  title: "Lab 1 - Image Processing",
  description: "## Lab 1: Image Processing\n\nImplement image filtering operations.",
  language: "python",
  sandbox_enabled: true,
  canvas_ref: "canvas-lab-1",
  base_points: 100,
  extra_credit_points: 0,
  entrypoint_path: "image_processor.py",
  scoring_items: [
    {
      key: "test_invert",
      label: "Invert Filter",
      points: 40,
      extra_credit: false,
      pytest_marker: "ag_key('test_invert')",
      item_type: "pytest",
      rubric_group_key: "functional",
    },
    {
      key: "test_grayscale",
      label: "Grayscale Filter",
      points: 40,
      extra_credit: false,
      pytest_marker: "ag_key('test_grayscale')",
      item_type: "pytest",
      rubric_group_key: "functional",
    },
    {
      key: "test_ast",
      label: "AST Safety Check",
      points: 20,
      extra_credit: false,
      pytest_marker: "ag_key('test_ast')",
      item_type: "pytest",
      rubric_group_key: "style",
    },
  ],
  rubric_groups: [
    { key: "functional", label: "Functional Requirements" },
    { key: "style", label: "Code Structure & Policy" },
  ],
  artifacts: [
    {
      artifact_key: "test_solution",
      artifact_type: "pytest_file",
      display_filename: "test_image_processor.py",
      size_bytes: 2048,
    },
  ],
  config: {
    description: "## Lab 1: Image Processing\n\nImplement image filtering operations.",
    bundle: {
      entrypoint: "image_processor.py",
      file_requirements: [
        {
          paths: ["image_processor.py"],
        },
      ],
    },
    scoring_items: [
      {
        key: "test_invert",
        label: "Invert Filter",
        points: 40,
        extra_credit: false,
        pytest_marker: "ag_key('test_invert')",
        item_type: "pytest",
        rubric_group_key: "functional",
      },
    ],
  },
  effective_allowed_concepts: ["variables", "conditionals", "functions", "lists"],
};

export const MOCK_RUN_SUMMARY: RunSummary = {
  id: 101,
  status: "complete",
  total_submission_count: 24,
  success_count: 21,
  warning_count: 2,
  failure_count: 1,
  timeout_count: 0,
  created_at: new Date(Date.now() - 3600000).toISOString(),
  review_expires_at: new Date(Date.now() + 82800000).toISOString(),
  retention_state: "available",
};

export const MOCK_RUN_DETAILS: RunDetailsResponse = {
  run_id: 101,
  status: "complete",
  requires_manual_grading: false,
  completed_students: 24,
  total_students: 24,
  exports_ready: true,
  students: [
    {
      student_name: "John Doe",
      canvas_id: "1001",
      bundle_files: ["image_processor.py"],
      bundle_file_count: 1,
      score: 100,
      max_score: 100,
      status: "success",
      feedback_preview: "All tests passed cleanly.",
      feedback_html: "<p>All 3 tests passed cleanly.</p>",
      manual_results: {},
      overall_comment: "",
      automated_results: [
        {
          key: "test_invert",
          label: "Invert Filter",
          outcome: "passed",
          passed: true,
          points_awarded: 40,
          points: 40,
        },
        {
          key: "test_grayscale",
          label: "Grayscale Filter",
          outcome: "passed",
          passed: true,
          points_awarded: 40,
          points: 40,
        },
        {
          key: "test_ast",
          label: "AST Safety Check",
          outcome: "passed",
          passed: true,
          points_awarded: 20,
          points: 20,
        },
      ],
      automated_score: 100,
      automated_max_score: 100,
    },
    {
      student_name: "Jane Smith",
      canvas_id: "1002",
      bundle_files: ["image_processor.py"],
      bundle_file_count: 1,
      score: 80,
      max_score: 100,
      status: "warning",
      feedback_preview: "Grayscale filter failed assertion.",
      feedback_html: "<p>Grayscale filter failed assertion on edge case.</p>",
      manual_results: {},
      overall_comment: "",
      automated_results: [
        {
          key: "test_invert",
          label: "Invert Filter",
          outcome: "passed",
          passed: true,
          points_awarded: 40,
          points: 40,
        },
        {
          key: "test_grayscale",
          label: "Grayscale Filter",
          outcome: "failed",
          passed: false,
          points_awarded: 0,
          points: 40,
        },
        {
          key: "test_ast",
          label: "AST Safety Check",
          outcome: "passed",
          passed: true,
          points_awarded: 20,
          points: 20,
        },
      ],
      automated_score: 80,
      automated_max_score: 100,
    },
  ],
};

export const MOCK_STUDENT_FILES: StudentFile[] = [
  {
    filepath: "image_processor.py",
    size_bytes: 840,
    previewable: true,
    preview_kind: "text",
  },
];

export const MOCK_ADMIN_USERS = [
  {
    id: 1,
    email: "dev.staff@uvu.edu",
    display_name: "Lead Instructor",
    is_active: true,
  },
  {
    id: 2,
    email: "dev.ia@uvu.edu",
    display_name: "Teaching Assistant",
    is_active: true,
  },
];

export const MOCK_ADMIN_ACCESS: StaffAccessRecord[] = [
  {
    id: 1,
    user_id: 1,
    user_email: "dev.staff@uvu.edu",
    user_name: "Lead Instructor",
    role_id: 1,
    role_name: "admin",
    course_id: 1,
    course_code: "CS 1410",
    section_id: null,
    section_crn: null,
    is_active: true,
  },
];

export const MOCK_SECTIONS: SectionAdminDetail[] = [
  {
    id: 1,
    course_id: 1,
    crn: "12345",
    is_active: true,
  },
  {
    id: 2,
    course_id: 1,
    crn: "12346",
    is_active: true,
  },
];

export const MOCK_MONITORING: MonitoringStats = {
  active_runs_count: 0,
  queued_runs_count: 0,
  sandbox_runs_last_hour: 4,
  total_token_usage: 12400,
  cleanup_service_healthy: true,
  cleanup_last_checked_at: new Date().toISOString(),
  cleanup_failed_runs: 0,
  cleanup_overdue_runs: 0,
  cleanup_orphan_errors: 0,
  dispatch_service_healthy: true,
  waiting_executions: 0,
  active_executions: 0,
};

export const MOCK_AUDIT_RECORDS: AuditRecord[] = [
  {
    id: 1,
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    event: "official.run_completed",
    workflow_type: "official",
    actor_user_id: 1,
    course_id: "CS 1410",
    assignment_id: "lab1",
    run_id: 101,
    status_code: 200,
    payload: {
      action: "batch_grade",
      submission_count: 24,
      exports_retained: true,
    },
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    event: "audit.pii_redacted",
    workflow_type: "official",
    actor_user_id: 1,
    course_id: "CS 1410",
    assignment_id: "lab1",
    run_id: 101,
    status_code: 200,
    payload: {
      rule: "canvas_filename",
      original_length: 38,
      replacement: "submission.py",
    },
  },
  {
    id: 3,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    event: "auth.access_denied",
    workflow_type: "official",
    actor_user_id: null,
    course_id: null,
    assignment_id: null,
    run_id: null,
    status_code: 403,
    payload: {
      endpoint: "/api/v1/staff/admin/courses",
      reason: "insufficient_role",
    },
  },
  {
    id: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4).toISOString(),
    event: "sandbox.run_completed",
    workflow_type: "sandbox",
    actor_user_id: null,
    course_id: "CS 1410",
    assignment_id: "lab1",
    run_id: 102,
    status_code: 200,
    payload: {
      student_score: 100,
      execution_seconds: 1.24,
    },
  },
];

export const MOCK_AUDIT_STATS: AuditStatsResponse = {
  total_events: 4,
  events_24h: 4,
  pii_redacted_count: 1,
  access_denied_count: 1,
  event_counts: {
    "official.run_completed": 1,
    "audit.pii_redacted": 1,
    "auth.access_denied": 1,
    "sandbox.run_completed": 1,
  },
};

export const MOCK_AUDIT_VERIFICATION: AuditVerificationResponse = {
  compliant: true,
  records_scanned: 4,
  violations_count: 0,
  violations: [],
  checked_at: new Date().toISOString(),
  disclaimer:
    "Pattern verification verifies absence of known log PII patterns (Canvas filenames, student paths, emails, UUIDs, U-numbers) in allowlisted audit fields. It does not verify student names or grades in unredacted student code.",
};
