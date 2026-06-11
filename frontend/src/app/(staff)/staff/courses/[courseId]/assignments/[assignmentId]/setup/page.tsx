import { apiClient } from "@/lib/api/client";

type Props = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

export default async function AssignmentSetupPage({ params }: Props) {
  const { courseId, assignmentId } = await params;
  const setup = await apiClient.getStaffAssignmentSetup(courseId, assignmentId);

  return (
    <main>
      <h1>{setup.title}</h1>
      <p>
        {setup.base_points} base points, {setup.extra_credit_points} extra credit points
      </p>
      <p>Entrypoint: {setup.entrypoint_path}</p>
      <h2>Scoring Items</h2>
      <ul>
        {setup.scoring_items.map((item) => (
          <li key={item.key}>
            {item.label}: {item.points} points
            {item.extra_credit ? " extra credit" : ""}
          </li>
        ))}
      </ul>
    </main>
  );
}
