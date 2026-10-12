import SandboxCoursesClient from "@/features/courses/sandbox-courses-client";

export const dynamic = "force-dynamic";

// Courses load in the browser: the API is reachable only from clients on the campus VPN.
export default function Page() {
    return <SandboxCoursesClient />;
}
