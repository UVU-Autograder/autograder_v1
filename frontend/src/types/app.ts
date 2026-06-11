export type AppRole = "admin" | "instructor" | "IA" | "student";

export type UploadQuota = {
  limit: number;
  window_seconds: number;
  remaining: number;
  reset_at: string;
};

export type CourseSummary = {
  id: string;
  title: string;
  term: string;
};

export type StaffCourseSummary = CourseSummary & {
  assignment_count: number;
};

export type SandboxCourse = CourseSummary & {
  sandbox_enabled_assignments: number;
};

export type ScoringItem = {
  key: string;
  label: string;
  points: number;
  extra_credit: boolean;
  pytest_marker: string;
};

export type CompletionRequirement = {
  key: string;
  label: string;
  test_keys: string[];
  minimum_passed: number;
};

export type SandboxAssignmentSummary = {
  id: string;
  course_id: string;
  title: string;
  sandbox_enabled: boolean;
  language: string;
  due_label: string | null;
  max_score: number;
  upload_quota: UploadQuota;
};

export type SandboxAssignmentDetail = SandboxAssignmentSummary & {
  description: string;
  accepted_bundle_types: string[];
  max_upload_bytes: number;
  constraints: { label: string; value: string }[];
  rubric: ScoringItem[];
  completion_requirements: CompletionRequirement[];
};

export type StaffAssignmentSummary = {
  id: string;
  course_id: string;
  title: string;
  language: string;
  due_label: string | null;
  sandbox_enabled: boolean;
  base_points: number;
  extra_credit_points: number;
};

export type ArtifactMetadata = {
  artifact_key: string;
  artifact_type: "pytest_file" | "model_solution" | "support_file";
  display_filename: string | null;
  size_bytes: number | null;
  sha256: string | null;
};

export type StaffAssignmentSetup = {
  course_id: string;
  assignment_id: string;
  title: string;
  language: string;
  due_label: string | null;
  sandbox_enabled: boolean;
  base_points: number;
  extra_credit_points: number;
  required_files: string[];
  entrypoint_path: string;
  concept_additions: string[];
  scoring_items: ScoringItem[];
  completion_requirements: CompletionRequirement[];
  artifacts: ArtifactMetadata[];
};
