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
  if (pathname.startsWith("/staff")) {
    if (pathname === "/staff/courses" || pathname === "/staff/courses/") {
      return "/sandbox";
    }
    const courseMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/?$/);
    if (courseMatch) {
      return `/sandbox/${courseMatch[1]}`;
    }
    const assignmentMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/assignments\/([^\/]+)/);
    if (assignmentMatch) {
      return `/sandbox/${assignmentMatch[1]}/assignments/${assignmentMatch[2]}`;
    }
    return null;
  }

  if (pathname.startsWith("/sandbox")) {
    if (pathname === "/sandbox" || pathname === "/sandbox/") {
      return "/staff/courses";
    }
    const assignmentMatch = pathname.match(/^\/sandbox\/([^\/]+)\/assignments\/([^\/]+)\/?$/);
    if (assignmentMatch) {
      return `/staff/courses/${assignmentMatch[1]}/assignments/${assignmentMatch[2]}/setup`;
    }
    const courseMatch = pathname.match(/^\/sandbox\/([^\/]+)\/?$/);
    if (courseMatch) {
      return `/staff/courses/${courseMatch[1]}`;
    }
    return null;
  }

  return null;
}

function hasStaffToken(): boolean {
  if (typeof window === "undefined") return false;
  return Boolean(localStorage.getItem("token") || sessionStorage.getItem("token"));
}

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const isStaffArea = pathname.startsWith("/staff");
  const isSandboxArea = pathname.startsWith("/sandbox");
  const isStaffLoggedIn = isStaffArea && pathname !== "/staff/login" && hasStaffToken();
  const oppositePath = getOppositePath(pathname);

  const switchRole = () => {
    if (oppositePath) {
      router.push(oppositePath);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("displayName");
    sessionStorage.removeItem("token");
    router.push("/staff/login");
  };

  return (
    <div className="sticky top-0 z-50 flex h-15 w-full items-center justify-between border-b border-gray-300 bg-background px-6">
      <NavigationMenu>
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuLink href={isStaffArea ? "/staff/courses" : "/sandbox"}>
              Dashboard
            </NavigationMenuLink>
          </NavigationMenuItem>
          {isSandboxArea && (
            <NavigationMenuItem>
              <NavigationMenuLink href="/sandbox">
                Sandbox
              </NavigationMenuLink>
            </NavigationMenuItem>
          )}
        </NavigationMenuList>
      </NavigationMenu>
      <div className="flex shrink-0 items-center gap-2">
        {isStaffLoggedIn && (
          <Button variant="outline" onClick={handleLogout}>
            Sign out
          </Button>
        )}
        {oppositePath && (
          <Button onClick={switchRole}>
            {isStaffArea ? "Switch to Student View" : "Switch to Staff View"}
          </Button>
        )}
      </div>
    </div>
  );
}
