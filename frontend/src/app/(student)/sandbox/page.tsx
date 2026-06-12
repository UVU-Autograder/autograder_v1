import { apiClient } from "@/lib/api/client";

export default async function SandboxCoursesPage() {
  const { courses } = await apiClient.listSandboxCourses();

  return (
    <main>
      <h1>Sandbox Courses</h1>
      <ul>
        {courses.map((course) => (
          <li key={course.id}>
            <a href={`/sandbox/${course.id}`}>{course.title}</a>
            <span> {course.term}</span>
            <span> {course.sandbox_enabled_assignments} assignments</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
