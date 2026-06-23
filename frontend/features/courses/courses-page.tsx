import { SandboxCoursesResponse, StaffCoursesResponse } from "@/features/courses/types";
import CourseCard from "@/features/courses/coursecard";

type ViewMode = "sandbox" | "staff";

export default function CoursesPage({
  data,
  mode,
}: {
  data: SandboxCoursesResponse | StaffCoursesResponse;
  mode: ViewMode;
}) {
  return (
    <div className="w-full flex justify-center pt-8">
    	<div className="w-full max-w-7xl px-4">
        {data.courses.length === 0 ? (
          <p className="text-center text-muted-foreground">No courses available yet.</p>
        ) : (
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				{data.courses.map((course) => (
					<CourseCard key={course.id} course={course} mode={mode} />
				))}
			</div>
        )}
    	</div>
    </div>
  );
}