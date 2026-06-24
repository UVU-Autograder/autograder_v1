import { redirect } from "next/navigation";

type PageProps = {
  params: Promise<{ courseId: string }>;
};

export default async function Page({ params }: PageProps) {
  const { courseId } = await params;
  redirect(`/staff/courses/${courseId}/assignments`);
}
