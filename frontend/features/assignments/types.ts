

export type Constraint = {
    label: string;
    value: string;
}

type RubricItem = {
    key: string;
    label: string;
    points: number;
    extra_credit: boolean;
    pytest_marker: string | null;
    item_type: string;
    rubric_group_key: string | null;
}

type UploadQuota = {
    limit: number;
    window_seconds: number;
    remaining: number;
    reset_at: string;
}

export type AssignmentsDetails = {
    id: string;
    course_id: string;
    title: string;
    sandbox_enabled: boolean;
    language: string;
    max_score: number;
    upload_quota: UploadQuota;
}

export type Assignment = AssignmentsDetails & {
    description: string;
    accepted_bundle_types: string[];
    max_upload_bytes: number;
    constraints: Constraint[];
    allowed_concepts?: string[];
    rubric: RubricItem[];
    rubric_groups: [];
    completion_requirements: [];
}

export type AssignmentsResponse = {
    course_id: string;
    assignments: AssignmentsDetails[];
}

export type RunState = "queue" | "run" | "complete" | "failure";

export type RunStatusResponse = {
    run_id: string;
    state: RunState;
    queue_position: number | null;
    eta_band: string | null;
    message: string | null;
};

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
    sanitized_feedback: string;
    retention_notice: string;
};

export type SandboxCancelResponse = {
    run_id: string;
    state: string;
    message: string;
};

export type ConceptMetadata = {
    key: string;
    title: string;
    syntax_patterns: string[];
    nodes: string[];
};