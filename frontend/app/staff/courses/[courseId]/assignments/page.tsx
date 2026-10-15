import AssignmentsClient from "@/features/assignments/assignments-client";

type PageProps = {
    params: Promise<{ courseId: string }>;
}

export const dynamic = "force-dynamic";

// Assignments load in the browser: the API is reachable only from clients on the campus VPN.
export default async function Page({ params }: PageProps) {
    const { courseId } = await params;
    return <AssignmentsClient courseId={courseId} mode="staff" />;
}
