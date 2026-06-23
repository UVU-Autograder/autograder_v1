"use client";

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu"
import { Button } from "@/components/ui/button";
import { usePathname, useRouter } from "next/navigation";

function getOppositePath(pathname: string): string | null {
  // 1. Staff side -> Student side
  if (pathname.startsWith("/staff")) {
    if (pathname === "/staff/courses" || pathname === "/staff/courses/") {
      return "/sandbox";
    }
    // Match /staff/courses/[courseId]
    const courseMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/?$/);
    if (courseMatch) {
      return `/sandbox/${courseMatch[1]}`;
    }
    // Match /staff/courses/[courseId]/assignments/[assignmentId]/...
    const assignmentMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/assignments\/([^\/]+)/);
    if (assignmentMatch) {
      return `/sandbox/${assignmentMatch[1]}/assignments/${assignmentMatch[2]}`;
    }
    return null;
  }

  // 2. Student side -> Staff side
  if (pathname.startsWith("/sandbox")) {
    if (pathname === "/sandbox" || pathname === "/sandbox/") {
      return "/staff/courses";
    }
    // Match /sandbox/[courseId]/assignments/[assignmentId]
    const assignmentMatch = pathname.match(/^\/sandbox\/([^\/]+)\/assignments\/([^\/]+)\/?$/);
    if (assignmentMatch) {
      return `/staff/courses/${assignmentMatch[1]}/assignments/${assignmentMatch[2]}/setup`;
    }
    // Match /sandbox/[courseId]
    const courseMatch = pathname.match(/^\/sandbox\/([^\/]+)\/?$/);
    if (courseMatch) {
      return `/staff/courses/${courseMatch[1]}`;
    }
    return null;
  }

  return null;
}

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const isStaffOrAdmin = pathname.startsWith("/staff") || pathname.startsWith("/admin");
  const oppositePath = getOppositePath(pathname);

  const switchRole = () => {
    if (oppositePath) {
      router.push(oppositePath);
    }
  };

  return (
    <div className="sticky top-0 z-50 flex h-15 w-full items-center justify-between border-b border-gray-300 bg-background px-6">
      <NavigationMenu>
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuLink href={isStaffOrAdmin ? "/staff/courses" : "/sandbox"}>
              Dashboard
            </NavigationMenuLink>
          </NavigationMenuItem>
          {isStaffOrAdmin && (
            <NavigationMenuItem>
              <NavigationMenuLink href="/admin">
                Admin
              </NavigationMenuLink>
            </NavigationMenuItem>
          )}
          {!isStaffOrAdmin && (
            <NavigationMenuItem>
              <NavigationMenuLink href="/sandbox/cs1400">
                Sandbox
              </NavigationMenuLink>
            </NavigationMenuItem>
          )}
        </NavigationMenuList>
      </NavigationMenu>
      {oppositePath && (
        <Button onClick={switchRole} className="shrink-0">
          {isStaffOrAdmin ? "Switch to Student View" : "Switch to Staff View"}
        </Button>
      )}
    </div>
  );
}