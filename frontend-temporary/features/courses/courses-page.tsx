import Link from "next/link";
import { BookOpenIcon } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Course, CoursesResponse } from "@/features/courses/types";

function assignmentCountLabel(count: number): string {
  if (count === 1) return "1 available assignment";
  return `${count} available assignments`;
}

export default function CoursesPage({ data }: { data: CoursesResponse }) {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-2">
        <h1 className="font-heading text-3xl font-semibold tracking-tight">
          Courses
        </h1>
        <p className="text-muted-foreground">
          Browse available courses.
        </p>
      </header>

      {data.courses.length === 0 ? (
        <p className="text-muted-foreground">No courses available.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.courses.map((course: Course) => (
            <Link
              key={course.id}
              href={`/courses/${course.id}`}
              className="group block h-full"
            >
              <Card className="h-full transition-shadow group-hover:shadow-md">
                <CardHeader>
                  <CardTitle>{course.title}</CardTitle>
                  <CardDescription>{course.term}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <BookOpenIcon className="size-4 shrink-0" />
                    <span>
                      {assignmentCountLabel(course.sandbox_enabled_assignments)}
                    </span>
                  </div>
                </CardContent>
                <CardFooter className="text-sm text-muted-foreground">
                  View course
                </CardFooter>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
