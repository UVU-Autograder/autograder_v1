import { CoursesResponse } from "@/features/courses/types";
import CourseCard from "@/features/courses/coursecard";

export default function CoursesPage({ data }: { data: CoursesResponse }) {
  return (
    <div className="w-full flex justify-center pt-8">
    	<div className="w-full max-w-7xl px-4">
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				{data.courses.map((course) => (
					<CourseCard key={course.id} course={course} />
				))}
			</div>  
    	</div>
    </div>
  );
}