import { getSandboxCourses } from "@/features/courses/api";
import CoursesPage from "@/features/courses/courses-page";

export const dynamic = "force-dynamic";

export default async function Page() {
    try {
        const data = await getSandboxCourses();
        return <CoursesPage data={data} mode="sandbox" />;
    } catch {
        throw new Error("Failed to load sandbox courses.");
    }
}
