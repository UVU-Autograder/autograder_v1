import { apiClient } from "@/lib/api/client";

type Props = {
  params: Promise<{ courseId: string; assignmentId: string }>;
};

export default async function AssignmentArtifactsPage({ params }: Props) {
  const { courseId, assignmentId } = await params;
  const { artifacts } = await apiClient.listAssignmentArtifacts(courseId, assignmentId);

  return (
    <main>
      <h1>Assignment Artifacts</h1>
      <ul>
        {artifacts.map((artifact) => (
          <li key={artifact.artifact_key}>
            {artifact.artifact_key}: {artifact.artifact_type}
            {artifact.display_filename ? ` (${artifact.display_filename})` : ""}
          </li>
        ))}
      </ul>
    </main>
  );
}
