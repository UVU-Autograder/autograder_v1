import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { getAssignment } from "@/features/assignments/api";
import AssignmentsPage from "@/features/assignments/workspace/assignment-page";
import { AssignmentFileProvider } from "@/features/assignments/workspace/assingment-file-context";
import { AssignmentSidebar } from "@/features/assignments/workspace/sidebar";

type PageProps = {
    params: Promise<{ courseId: string; assignmentId: string }>;
}

export default async function Page({ params }: PageProps) {
    const { courseId, assignmentId } = await params;
    const assignment = await getAssignment(courseId, assignmentId);
    
    return (
        <AssignmentFileProvider>
        <SidebarProvider className="h-svh min-h-0">
            <AssignmentSidebar assignment={assignment} courseId={courseId} className="mt-15" />
            <SidebarInset className="min-h-0 flex-1 overflow-hidden">
                <AssignmentsPage
                  courseId={courseId}
                  assignmentId={assignmentId}
                  maxScore={assignment.max_score}
                />
            </SidebarInset>
        </SidebarProvider>
    </AssignmentFileProvider>
    )
}
