import { getAssignments } from "@/features/assignments/api";
import AssignmentsPage from "@/features/assignments/assignments-page";

type PageProps = {
    params: Promise<{ courseId: string }>;
}

export const dynamic = "force-dynamic";

export default async function Page({ params }: PageProps) {
    const { courseId } = await params;
    try {
        const data = await getAssignments(courseId);
        return <AssignmentsPage data={data} mode="staff" />;
    } catch {
        throw new Error("Failed to load assignments.");
    }
}
