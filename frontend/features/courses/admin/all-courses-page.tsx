import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";
import { StaffCoursesResponse } from "@/features/courses/types";

export default function AllCoursesPage({ data }: { data: StaffCoursesResponse }) {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8">
      <Button variant="ghost" size="sm" className="mb-4 -ml-2" asChild>
        <Link href="/staff/admin">
          <ArrowLeftIcon />
          Back to admin
        </Link>
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold tracking-tight">All Courses</h1>
        <Button disabled>Add course</Button>
      </div>

      {data.courses.length === 0 ? (
        <p className="text-muted-foreground">No courses available yet.</p>
      ) : (
        <div className="flex w-full flex-col gap-2">
          {data.courses.map((course) => (
            <Card key={course.id} className="py-3 transition-shadow hover:shadow-md">
              <CardContent className="flex items-center gap-3 py-0">
                <Link
                  href={`/staff/courses/${course.id}`}
                  className="min-w-0 flex-1"
                >
                  <div className="space-y-0.5">
                    <CardTitle className="truncate text-base">
                      {course.title}
                    </CardTitle>
                    <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-0 text-xs">
                      <span className="uppercase tracking-wider">{course.id}</span>
                      <span>{course.term}</span>
                      <span>
                        {course.assignment_count}{" "}
                        {course.assignment_count === 1 ? "assignment" : "assignments"}
                      </span>
                    </CardDescription>
                  </div>
                </Link>
                <div className="flex shrink-0 gap-2">
                  <Button variant="outline" size="sm" disabled>
                    Edit
                  </Button>
                  <Button variant="destructive" size="sm" disabled>
                    Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
