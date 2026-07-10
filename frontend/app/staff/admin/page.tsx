import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";

const adminLinks = [
  {
    href: "/staff/admin/courses",
    title: "Courses",
    description: "Manage courses, terms, assignments, and roles",
  },
  {
    href: "/staff/admin/access",
    title: "Access",
    description: "Manage instructors and IAs access control grants",
  },
  {
    href: "/staff/admin/monitoring",
    title: "Monitoring",
    description: "View active runs, queue size, and token usage statistics",
  },
];

export default function AdminPage() {
  return (
    <div className="mx-auto w-full max-w-4xl px-4 pt-8">
      <h1 className="mb-6 text-2xl font-semibold tracking-tight">Admin</h1>

      <div className="flex w-full flex-col gap-2">
        {adminLinks.map((link) => (
          <Link key={link.href} href={link.href} className="block">
            <Card className="cursor-pointer py-3 transition-shadow hover:shadow-md">
              <CardContent className="py-0">
                <CardTitle className="text-base">{link.title}</CardTitle>
                <CardDescription>{link.description}</CardDescription>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
