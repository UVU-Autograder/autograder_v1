export type Constraint = {
    label: string;
    value: string;
};

export type RubricItem = {
    id?: string;
    key: string;
    label: string;
    points: number;
    extra_credit: boolean;
    pytest_marker: string | null;
    item_type: "pytest" | "manual";
    rubric_group_key: string | null;
    inputs?: string[] | null;
    outputs?: string[] | null;
};

export type RubricGroup = {
    key: string;
    label: string;
    item_keys?: string[];
};

export type CompletionRequirement = {
    key: string;
    label: string;
    test_keys: string[];
    minimum_passed: number;
};

export type StaffArtifact = {
    artifact_key: string;
    artifact_type: string;
    display_filename: string | null;
    size_bytes: number | null;
    sha256?: string | null;
};

export type FileRequirementConfig = {
    label: string;
    paths?: string[] | null;
    pattern?: string | null;
};

export type BundleConfig = {
    entrypoint: string;
    file_requirements?: FileRequirementConfig[];
};

export type ArtifactConfig = {
    type: "pytest_file" | "model_solution" | "support_file";
    display_filename?: string | null;
};

export type AssignmentConfigV1 = {
    description?: string | null;
    bundle: BundleConfig;
    artifacts?: Record<string, ArtifactConfig>;
    concepts?: {
        allowlist?: string[];
        denylist?: string[];
    };

    scoring_items: RubricItem[];
    rubric_groups?: RubricGroup[];
    completion_requirements?: CompletionRequirement[];
    dependencies?: string[];
};

type UploadQuota = {
    limit: number;
    window_seconds: number;
    remaining: number;
    reset_at: string;
};

export type AssignmentsDetails = {
    id: string;
    course_id: string;
    title: string;
    description?: string | null;
    sandbox_enabled: boolean;
    language: string;
    max_score: number;
    upload_quota: UploadQuota;
    module_name?: string | null;
};

export type Assignment = AssignmentsDetails & {
    description: string;
    accepted_bundle_types: string[];
    max_upload_bytes: number;
    constraints: Constraint[];
    allowed_concepts?: string[];
    rubric: RubricItem[];
    rubric_groups: RubricGroup[];
    completion_requirements: CompletionRequirement[];
    config?: AssignmentConfigV1;
};

export type AssignmentsResponse = {
    course_id: string;
    assignments: AssignmentsDetails[];
};

export type RunState = "queue" | "run" | "complete" | "failure";

export type RunCounters = {
    total: number;
    queued: number;
    running: number;
    completed: number;
    failed: number;
    warnings: number;
};

export type RunStatusResponse = {
    run_id: string;
    state: RunState;
    queue_position: number | null;
    eta_band: string | null;
    message: string | null;
    counters?: RunCounters;
};

export function runProcessedCount(counters: RunCounters | undefined): number {
    if (!counters) return 0;
    return counters.completed + counters.failed;
}

export type SandboxRunCreateResponse = {
    run_id: string;
    sandbox_session: string;
    status_url: string;
    result_url: string;
    upload_quota: UploadQuota;
    initial_status: RunStatusResponse;
};

export type SandboxTestSummary = {
    label: string;
    status: "passed" | "failed" | "warning" | "not_run";
    points_awarded: number;
    points_possible: number;
    message: string;
    actual?: string;
    expected?: string;
    your_value?: string | null;
    expected_value?: string | null;
    expected_input?: string | null;
    group_key?: string | null;
};

export type RubricGroupResultResponse = {
    group_key: string;
    label: string;
    points_earned: number;
    points_possible: number;
    items: SandboxTestSummary[];
};

export type SandboxWarning = {
    code: string;
    message: string;
};

export type SandboxRunResultResponse = {
    run_id: string;
    state: "complete" | "failure";
    projected_score: number;
    max_score: number;
    warnings: SandboxWarning[];
    test_summaries: SandboxTestSummary[];
    rubric_groups?: RubricGroupResultResponse[];
    sanitized_feedback: string;
    retention_notice?: string | null;
    raw_output?: string | null;
};

export type SandboxCancelResponse = {
    run_id: string;
    state: string;
    message: string;
};

export type SandboxAiFeedbackResponse = {
    run_id: string;
    ai_feedback: string;
    model: string;
};

export type ConceptMetadata = {
    key: string;
    title: string;
    syntax_patterns: string[];
    nodes: string[];
};

export type StaffAssignmentSetup = {
    course_id: string;
    assignment_id: string;
    title: string;
    description?: string | null;
    language: string;
    sandbox_enabled: boolean;
    canvas_ref: string | null;
    base_points: number;
    extra_credit_points: number;
    entrypoint_path: string;
    scoring_items: RubricItem[];
    rubric_groups?: RubricGroup[];
    completion_requirements?: CompletionRequirement[];
    artifacts: StaffArtifact[];
    config: AssignmentConfigV1;
    module_id?: number | null;
    effective_allowed_concepts?: string[];
};

export type AssignmentCreatePayload = {
    slug: string;
    title: string;
    description?: string | null;
    language: string;
    canvas_ref?: string | null;
    sandbox_enabled?: boolean;
    module_id?: number | null;
};
