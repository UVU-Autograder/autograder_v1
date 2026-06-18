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
    rubric: RubricItem[];
    rubric_groups: [];
    completion_requirements: [];
}

export type AssignmentsResponse = {
    course_id: string;
    assignments: AssignmentsDetails[];
}