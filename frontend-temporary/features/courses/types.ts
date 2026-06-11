export type Course = {
    id: string;
    title: string;
    term: string;
    sandbox_enabled_assignments: number;
}

export type CoursesResponse = {
    courses: Course[];
}