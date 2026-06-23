import { getAssignments } from "@/features/assignments/api";
import AssignmentsPage from "@/features/assignments/assignments-page";

export const dynamic = "force-dynamic";

type PageProps = {
    params: Promise<{ courseId: string }>;
}

export default async function Page({ params }: PageProps) {
    const { courseId } = await params;
    const data = await getAssignments(courseId);

    return <AssignmentsPage data={data} />;
}
