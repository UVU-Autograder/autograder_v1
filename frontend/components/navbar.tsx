"use client";

import Link from "next/link";
import Image from "next/image";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";
import { Button } from "@/components/ui/button";
import { usePathname, useRouter } from "next/navigation";
import { useSyncExternalStore } from "react";
import { ThemeToggle } from "@/components/theme-toggle";

function getOppositePath(pathname: string): string | null {
  if (pathname.startsWith("/staff")) {
    if (pathname === "/staff/courses" || pathname === "/staff/courses/") {
      return "/sandbox";
    }
    const courseMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/assignments\/?$/) || pathname.match(/^\/staff\/courses\/([^\/]+)\/?$/);
    if (courseMatch) {
      return `/sandbox/${courseMatch[1]}/assignments`;
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
      return `/staff/courses/${assignmentMatch[1]}/assignments/${assignmentMatch[2]}`;
    }
    const courseMatch = pathname.match(/^\/sandbox\/([^\/]+)\/assignments\/?$/) || pathname.match(/^\/sandbox\/([^\/]+)\/?$/);
    if (courseMatch) {
      return `/staff/courses/${courseMatch[1]}/assignments`;
    }
    return null;
  }

  return null;
}

function subscribeToStaffAuth(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  return () => window.removeEventListener("storage", onStoreChange);
}

function getStaffAuthSnapshot(): boolean {
  return Boolean(localStorage.getItem("token") || sessionStorage.getItem("token"));
}

function getStaffAuthServerSnapshot(): boolean {
  return false;
}

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const hasStaffToken = useSyncExternalStore(
    subscribeToStaffAuth,
    getStaffAuthSnapshot,
    getStaffAuthServerSnapshot
  );

  const isStaffArea = pathname.startsWith("/staff");
  const isStaffLoggedIn = hasStaffToken;

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

  const homeHref = isStaffArea ? "/staff/courses" : "/sandbox";

  return (
    <div className="sticky top-0 z-50 flex h-18 w-full items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center gap-6">
        {/* UVU Logo Link */}
        <Link href={homeHref} className="flex items-center gap-2 hover:opacity-90 transition-opacity">
          <Image
            src="/uvu-logo.png"
            alt="UVU Logo"
            width={256}
            height={256}
            unoptimized
            className="h-14 w-14 shrink-0 rounded-md object-contain"
          />
          <span className="font-bold text-xl text-slate-900 dark:text-slate-100 tracking-tight">
            Autograder
          </span>
        </Link>

        {/* Navigation Menu for Admin */}
        {hasStaffToken && (
          <NavigationMenu>
            <NavigationMenuList>
              <NavigationMenuItem>
                <NavigationMenuLink href="/staff/courses">
                  Admin
                </NavigationMenuLink>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <ThemeToggle />
        {isStaffLoggedIn && (
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Sign out
          </Button>
        )}
        {oppositePath && (
          <Button size="sm" onClick={switchRole}>
            {isStaffArea ? "Switch to Student View" : "Switch to Staff View"}
          </Button>
        )}
      </div>
    </div>
  );
}
