import { getSandboxCourses } from "@/features/courses/api";
import CoursesPage from "@/features/courses/courses-page";

export const dynamic = "force-dynamic";

export default async function Page() {
    let data: Awaited<ReturnType<typeof getSandboxCourses>>;
    try {
        data = await getSandboxCourses();
    } catch {
        throw new Error("Failed to load sandbox courses.");
    }
    return <CoursesPage data={data} mode="sandbox" />;
}
