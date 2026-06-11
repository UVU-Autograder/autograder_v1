import { getCourses } from "@/features/courses/api";
import CoursesPage from "@/features/courses/courses-page";

export default async function Page() {
    const data = await getCourses();

    return <CoursesPage data={data} />;
}