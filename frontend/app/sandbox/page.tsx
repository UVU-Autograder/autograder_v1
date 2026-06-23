import { getSandboxCourses } from "@/features/courses/api";
import CoursesPage from "@/features/courses/courses-page";

export const dynamic = "force-dynamic";

export default async function Page() {
    const data = await getSandboxCourses();

    return <CoursesPage data={data} />;
}
