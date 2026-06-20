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