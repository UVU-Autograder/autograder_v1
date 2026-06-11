import { apiClient } from "@/lib/api/client";

type Props = {
  params: Promise<{ courseId: string }>;
};

export default async function SandboxAssignmentsPage({ params }: Props) {
  const { courseId } = await params;
  const { assignments } = await apiClient.listSandboxAssignments(courseId);

  return (
    <main>
      <h1>Sandbox Assignments</h1>
      <ul>
        {assignments.map((assignment) => (
          <li key={assignment.id}>
            <a href={`/sandbox/${courseId}/assignments/${assignment.id}`}>
              {assignment.title}
            </a>
            <span> {assignment.max_score} points</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
