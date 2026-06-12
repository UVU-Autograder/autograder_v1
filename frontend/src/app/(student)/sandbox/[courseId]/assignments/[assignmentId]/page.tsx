import { apiClient } from "@/lib/api/client";

type Props = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

export default async function SandboxAssignmentPage({ params }: Props) {
  const { courseId, assignmentId } = await params;
  const assignment = await apiClient.getSandboxAssignment(courseId, assignmentId);

  return (
    <main>
      <h1>{assignment.title}</h1>
      <p>{assignment.description}</p>
      <p>
        {assignment.max_score} base points. {assignment.upload_quota.remaining} sandbox uploads remaining.
      </p>
      <h2>Scoring Items</h2>
      <ul>
        {assignment.rubric.map((item) => (
          <li key={item.key ?? item.label}>
            {item.label}: {item.points} points
            {item.extra_credit ? " extra credit" : ""}
          </li>
        ))}
      </ul>
    </main>
  );
}
