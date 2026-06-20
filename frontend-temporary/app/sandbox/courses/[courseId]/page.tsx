type CoursePageProps = {
    params: Promise<{ courseId: string }>;
}

export default async function Page({ params }: CoursePageProps) {
    const { courseId } = await params;
    return (
        <div>
            <h1>Course {courseId}</h1>
        </div>
    )
}