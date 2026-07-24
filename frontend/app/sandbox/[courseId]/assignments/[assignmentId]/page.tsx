import { getAssignment } from "@/features/assignments/api";
import AssignmentWorkspace from "@/features/assignments/workspace/assignment-page";
import { AssignmentFileProvider } from "@/features/assignments/workspace/assignment-file-context";

export const dynamic = "force-dynamic";

type PageProps = {
    params: Promise<{ courseId: string; assignmentId: string }>;
};

export default async function Page({ params }: PageProps) {
    const { courseId, assignmentId } = await params;
    const assignment = await getAssignment(courseId, assignmentId);
    
    return (
        <AssignmentFileProvider assignment={assignment}>
            <div className="h-full w-full min-h-0 flex flex-1 flex-col overflow-hidden">
                <AssignmentWorkspace
                  courseId={courseId}
                  assignmentId={assignmentId}
                  maxScore={assignment.max_score}
                  initialQuota={assignment.upload_quota}
                  assignment={assignment}
                />
            </div>
        </AssignmentFileProvider>
    );
}
