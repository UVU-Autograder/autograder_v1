"use client";

import Link from "next/link";
import Image from "next/image";
import { ShieldIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useSyncExternalStore } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { apiClient, isMockApiEnabled } from "@/lib/api-client";

export function getOppositePath(pathname: string): string | null {
  if (pathname.startsWith("/staff")) {
    if (
      pathname === "/staff/login" ||
      pathname === "/staff/login/" ||
      pathname === "/staff/courses" ||
      pathname === "/staff/courses/" ||
      pathname.startsWith("/staff/admin")
    ) {
      return "/sandbox";
    }

    const newAssignmentMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/assignments\/new\/?$/);
    if (newAssignmentMatch) {
      return `/sandbox/${newAssignmentMatch[1]}/assignments`;
    }

    const settingsMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/settings\/?$/);
    if (settingsMatch) {
      return `/sandbox/${settingsMatch[1]}/assignments`;
    }

    const assignmentMatch = pathname.match(/^\/staff\/courses\/([^\/]+)\/assignments\/([^\/]+)/);
    if (assignmentMatch) {
      return `/sandbox/${assignmentMatch[1]}/assignments/${assignmentMatch[2]}`;
    }

    const courseMatch = pathname.match(/^\/staff\/courses\/([^\/]+)/);
    if (courseMatch) {
      return `/sandbox/${courseMatch[1]}/assignments`;
    }

    return "/sandbox";
  }

  if (pathname.startsWith("/sandbox")) {
    if (pathname === "/sandbox" || pathname === "/sandbox/") {
      return "/staff/courses";
    }
    const assignmentMatch = pathname.match(/^\/sandbox\/([^\/]+)\/assignments\/([^\/]+)\/?$/);
    if (assignmentMatch) {
      return `/staff/courses/${assignmentMatch[1]}/assignments/${assignmentMatch[2]}`;
    }
    const courseMatch = pathname.match(/^\/sandbox\/([^\/]+)/);
    if (courseMatch) {
      return `/staff/courses/${courseMatch[1]}/assignments`;
    }
    return "/staff/courses";
  }

  return null;
}

function subscribeToStaffAuth(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener("roles-updated", onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener("roles-updated", onStoreChange);
  };
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

function subscribeMockApi(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  return () => window.removeEventListener("storage", onStoreChange);
}

function getMockApiSnapshot(): boolean {
  return isMockApiEnabled();
}

function getMockApiServerSnapshot(): boolean {
  return false;
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
  const isMockActive = useSyncExternalStore(
    subscribeMockApi,
    getMockApiSnapshot,
    getMockApiServerSnapshot,
  );
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
    router.replace("/staff/login");
  };

  const homeHref = isStaffArea ? "/staff/courses" : "/sandbox";

  return (
    <div className="sticky top-0 z-50 flex h-18 w-full items-center justify-between border-b border-header-border bg-header text-header-foreground px-6 shadow-xs">
      <div className="flex items-center gap-6">
        <Link href={homeHref} className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
          <Image
            src="/uvu-logo-green.png"
            alt="UVU Logo"
            width={256}
            height={256}
            unoptimized
            className="h-16 w-16 shrink-0 rounded-md object-contain dark:hidden"
          />
          <Image
            src="/uvu-logo-white.png"
            alt="UVU Logo"
            width={256}
            height={256}
            unoptimized
            className="hidden h-16 w-16 shrink-0 rounded-md object-contain dark:block"
          />
          <span className="font-bold text-xl text-primary dark:text-white tracking-tight">
            Autograder
          </span>
        </Link>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        {isMockActive && (
          <span className="rounded bg-amber-500/15 text-amber-900 border border-amber-600/30 dark:bg-white/15 dark:text-white dark:border-white/20 px-2 py-0.5 text-xs font-medium">
            Mock API
          </span>
        )}
        <ThemeToggle className="text-foreground/70 hover:text-foreground hover:bg-black/5 dark:text-white/80 dark:hover:text-white dark:hover:bg-white/15" />
        {isStaffArea && isAdmin && (
          <Button
            variant="ghost"
            size="sm"
            asChild
            className={
              pathname.startsWith("/staff/admin")
                ? "bg-black/10 text-foreground dark:bg-white/20 dark:text-white"
                : "text-foreground/70 hover:bg-black/5 hover:text-foreground dark:text-white/80 dark:hover:bg-white/15 dark:hover:text-white"
            }
          >
            <Link href="/staff/admin" className="flex items-center gap-1.5">
              <ShieldIcon className="h-4 w-4" />
              <span>Admin</span>
            </Link>
          </Button>
        )}
        {isStaffLoggedIn && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="border-foreground/25 bg-transparent text-foreground hover:bg-black/5 dark:border-white/30 dark:text-white dark:hover:bg-white/15 dark:hover:text-white"
          >
            Sign out
          </Button>
        )}
        {oppositePath && (
          <Button
            size="sm"
            asChild
            className="bg-primary text-primary-foreground hover:bg-primary/90 dark:bg-white dark:text-zinc-900 dark:hover:bg-white/90 font-medium shadow-xs border-0"
          >
            <Link href={oppositePath}>
              {isStaffArea ? "Student View" : "Staff View"}
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
