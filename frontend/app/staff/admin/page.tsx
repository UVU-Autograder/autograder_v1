import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { AdminPageHeader } from "@/components/admin-page-header";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { Button } from "@/components/ui/button";

const setupLinks = [
  {
    href: "/staff/admin/courses",
    title: "Courses",
    description: "Create courses, terms, and default concepts",
  },
  {
    href: "/staff/admin/access",
    title: "Access",
    description: "Grant instructor, IA, and admin roles",
  },
];

const operationsLinks = [
  {
    href: "/staff/admin/activity",
    title: "Activity Monitor",
    description: "Student practice velocity, attempt distributions, and error bottlenecks",
  },
  {
    href: "/staff/admin/monitoring",
    title: "Monitoring",
    description: "Queues, cleanup health, and token usage",
  },
  {
    href: "/staff/admin/logs",
    title: "Audit logs",
    description: "Search events and check FERPA redaction",
  },
];

function AdminLinkList({
  links,
}: {
  links: { href: string; title: string; description: string }[];
}) {
  return (
    <ul className="divide-y divide-border border-y border-border">
      {links.map((link) => (
        <li key={link.href}>
          <Link
            href={link.href}
            className="block py-3 px-1 transition-colors hover:bg-muted/40"
          >
            <div className="font-medium text-foreground">{link.title}</div>
            <p className="text-sm text-muted-foreground">{link.description}</p>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export default function AdminPage() {
  return (
    <div className="mx-auto w-full max-w-2xl px-4 pt-8 pb-12">
      <Breadcrumbs
        items={[
          { label: "Courses", href: "/staff/courses" },
          { label: "Admin" },
        ]}
      />
      <AdminPageHeader
        title="Admin"
        actions={
          <Button variant="outline" size="sm" asChild>
            <Link href="/staff/courses">
              <ArrowLeftIcon className="mr-1.5 h-4 w-4" />
              Back to courses
            </Link>
          </Button>
        }
      />

      <section className="mb-8 space-y-2">
        <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
          Setup
        </h2>
        <AdminLinkList links={setupLinks} />
      </section>

      <section className="space-y-2">
        <h2 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
          Operations
        </h2>
        <AdminLinkList links={operationsLinks} />
      </section>
    </div>
  );
}
