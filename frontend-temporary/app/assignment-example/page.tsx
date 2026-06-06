import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AssignmentsDataType, assignmentsResponse } from "@/fakedata/assignments-reponse";
import AssignmentsPage from "@/features/assignments/assignments-page";
import { AssignmentFileProvider } from "@/features/assignments/assingment-file-context";
import { AssignmentsSidebar } from "@/features/assignments/sidebar";

const data: AssignmentsDataType = assignmentsResponse;

export default function Page() {
  return (
    <AssignmentFileProvider>
        <SidebarProvider>
            <AssignmentsSidebar />
            <SidebarInset>
                <AssignmentsPage data={data} />
            </SidebarInset>
        </SidebarProvider>
    </AssignmentFileProvider>
  );
}