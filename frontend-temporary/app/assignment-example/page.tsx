import { AssignmentsDataType, assignmentsResponse } from "@/fakedata/assignments-reponse";
import AssignmentsPage from "@/features/assignments/assignments-page";

const data: AssignmentsDataType = assignmentsResponse;

export default function Page() {
  return (
    <AssignmentsPage data={data} />
  );
}