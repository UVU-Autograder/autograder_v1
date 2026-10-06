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
import { useEffect, useState, useSyncExternalStore } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { apiClient, isMockApiEnabled } from "@/lib/api-client";

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

function readStoredRoles(): string[] {
  try {
    const raw = localStorage.getItem("roles");
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((r) => typeof r === "string") : [];
  } catch {
    return [];
  }
}

function subscribeRoles(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener("roles-updated", onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener("roles-updated", onStoreChange);
  };
}

function getRolesSnapshot(): string {
  return JSON.stringify(readStoredRoles());
}

function getRolesServerSnapshot(): string {
  return "[]";
}

type AuthMeResponse = {
  email: string;
  display_name: string | null;
  roles: string[];
};

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const hasStaffToken = useSyncExternalStore(
    subscribeToStaffAuth,
    getStaffAuthSnapshot,
    getStaffAuthServerSnapshot
  );
  const rolesJson = useSyncExternalStore(
    subscribeRoles,
    getRolesSnapshot,
    getRolesServerSnapshot,
  );
  const [isMockActive, setIsMockActive] = useState(false);

  useEffect(() => {
    setIsMockActive(isMockApiEnabled());
  }, []);
  const roles: string[] = JSON.parse(rolesJson);
  const isAdmin = hasStaffToken && roles.includes("admin");

  useEffect(() => {
    if (!hasStaffToken) return;

    let cancelled = false;
    apiClient
      .get<AuthMeResponse>("/auth/me")
      .then((me) => {
        if (cancelled) return;
        localStorage.setItem("roles", JSON.stringify(me.roles ?? []));
        window.dispatchEvent(new Event("roles-updated"));
      })
      .catch(() => {
        // Keep whatever roles are already in localStorage.
      });

    return () => {
      cancelled = true;
    };
  }, [hasStaffToken]);

  const isStaffArea = pathname.startsWith("/staff");
  const isStaffLoggedIn = hasStaffToken;

  const oppositePath = getOppositePath(pathname);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("displayName");
    localStorage.removeItem("roles");
    sessionStorage.removeItem("token");
    window.dispatchEvent(new Event("roles-updated"));
    router.push("/staff/login");
  };

  const homeHref = isStaffArea ? "/staff/courses" : "/sandbox";

  return (
    <div className="sticky top-0 z-50 flex h-18 w-full items-center justify-between border-b border-border bg-background px-6">
      <div className="flex items-center gap-6">
        <Link href={homeHref} className="flex items-center gap-2 hover:opacity-90 transition-opacity">
          <Image
            src="/uvu-logo.png"
            alt="UVU Logo"
            width={256}
            height={256}
            unoptimized
            className="h-14 w-14 shrink-0 rounded-md object-contain"
          />
          <span className="font-bold text-xl text-foreground tracking-tight">
            Autograder
          </span>
        </Link>

        {hasStaffToken && isAdmin && (
          <NavigationMenu>
            <NavigationMenuList>
              <NavigationMenuItem>
                <NavigationMenuLink asChild>
                  <Link href="/staff/admin">Admin</Link>
                </NavigationMenuLink>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        {isMockActive && (
          <span className="rounded bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400 border border-amber-500/20">
            Mock API
          </span>
        )}
        <ThemeToggle />
        {isStaffLoggedIn && (
          <Button variant="outline" size="sm" onClick={handleLogout}>
            Sign out
          </Button>
        )}
        {oppositePath && (
          <Button size="sm" asChild>
            <Link href={oppositePath}>
              {isStaffArea ? "Switch to Student View" : "Switch to Staff View"}
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
