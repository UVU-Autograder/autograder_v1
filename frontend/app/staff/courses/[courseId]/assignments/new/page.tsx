import CreateAssignment from "@/features/assignments/create-assignment";

type PageProps = {
  params: Promise<{ courseId: string }>;
};

export default async function Page({ params }: PageProps) {
  const { courseId } = await params;
  return <CreateAssignment courseId={courseId} />;
}
