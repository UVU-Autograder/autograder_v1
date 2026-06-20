"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { SandboxCourse, StaffCourse } from "@/features/courses/types";
import { useBasePath } from "@/lib/view-context";

const colors = [
  "from-blue-500 to-blue-200",
  "from-green-500 to-green-200",
  "from-purple-500 to-purple-200",
  "from-red-500 to-red-200",
  "from-orange-500 to-orange-200",
];

// stable color based on course id (frontend-only logic)
function getColor(id: string) {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = id.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}


export default function CourseCard({ course }: { course: SandboxCourse | StaffCourse }) {
  const colorClass = getColor(course.id);
  const basePath = useBasePath();

  return (
    <Link href={`${basePath}/courses/${course.id}/assignments`} className="block">
      <Card className="overflow-hidden hover:shadow-lg transition-all cursor-pointer">

        {/* TOP COLOR BANNER (like CardMedia) */}
        <div className={`h-36 bg-gradient-to-br ${colorClass}`} />

        {/* CONTENT */}
        <CardHeader>
          <CardDescription className="uppercase tracking-wider text-xs">
            {course.id}
          </CardDescription>

          <CardTitle className="text-lg">
            {course.title}
          </CardTitle>
        </CardHeader>

        <CardContent>
          <p className="text-sm text-muted-foreground">
            {course.term}
          </p>

          <p className="text-sm mt-3 text-slate-600">
            Click to view assignments →
          </p>
        </CardContent>

      </Card>
    </Link>
  );
}