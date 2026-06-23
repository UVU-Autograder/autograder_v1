import { getAssignments } from "@/features/assignments/api";
import AssignmentsPage from "@/features/assignments/assignments-page";

export const dynamic = "force-dynamic";

type PageProps = {
    params: Promise<{ courseId: string }>;
}

export default async function Page({ params }: PageProps) {
    const { courseId } = await params;
    let data;
    try {
        data = await getAssignments(courseId);
    } catch {
        throw new Error("Failed to load assignments.");
    }
    return <AssignmentsPage data={data} mode="sandbox" />;
}
