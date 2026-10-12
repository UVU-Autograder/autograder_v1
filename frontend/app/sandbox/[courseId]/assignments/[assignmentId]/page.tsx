import AssignmentClient from "@/features/assignments/workspace/assignment-client";

export const dynamic = "force-dynamic";

type PageProps = {
    params: Promise<{ courseId: string; assignmentId: string }>;
};

// The assignment loads in the browser: the API is reachable only from clients on the campus VPN.
export default async function Page({ params }: PageProps) {
    const { courseId, assignmentId } = await params;
    return <AssignmentClient courseId={courseId} assignmentId={assignmentId} />;
}
