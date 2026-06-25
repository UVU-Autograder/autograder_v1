export type SandboxCourse = {
    id: string;
    title: string;
    term: string;
    sandbox_enabled_assignments: number;
}

export type SandboxCoursesResponse = {
    courses: SandboxCourse[];
}

export type StaffCourse = {
    id: string;
    title: string;
    term: string;
    assignment_count: number;
}

export type StaffCoursesResponse = {
    courses: StaffCourse[];
}

export type CourseAdminDetail = {
    id: number;
    code: string;
    title: string;
    term: string;
    is_active: boolean;
    instructor_id: number | null;
    instructor_email: string | null;
    ia_id: number | null;
    ia_email: string | null;
    default_concepts: string[];
    section_count: number;
    assignment_count: number;
}