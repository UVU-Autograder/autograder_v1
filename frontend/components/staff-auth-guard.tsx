"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useRouter, usePathname } from "next/navigation";

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

export function StaffAuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isLoginPage = pathname === "/staff/login" || Boolean(pathname?.startsWith("/staff/login"));

  const hasStaffToken = useSyncExternalStore(
    subscribeToStaffAuth,
    getStaffAuthSnapshot,
    getStaffAuthServerSnapshot
  );

  useEffect(() => {
    if (isLoginPage) return;

    if (!hasStaffToken) {
      router.push("/staff/login");
      return;
    }

    const handleAuthError = () => {
      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      localStorage.removeItem("lastActivity");
      window.dispatchEvent(new Event("storage"));
      router.push("/staff/login");
    };

    // Inactivity timeout: 60 minutes (3,600,000ms) to match standard session lifetime
    const INACTIVITY_TIMEOUT = 60 * 60 * 1000;

    const checkInactivity = () => {
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      if (!token) return;

      const lastActivity = parseInt(localStorage.getItem("lastActivity") || "0");
      if (lastActivity === 0) return;

      const elapsed = Date.now() - lastActivity;
      if (elapsed >= INACTIVITY_TIMEOUT) {
        localStorage.removeItem("token");
        sessionStorage.removeItem("token");
        localStorage.removeItem("lastActivity");
        window.dispatchEvent(new Event("storage"));
        router.push("/staff/login?reason=timeout");
      }
    };

    let lastRecorded = 0;
    const updateActivity = () => {
      const now = Date.now();
      if (now - lastRecorded < 15000) return;
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      if (token) {
        lastRecorded = now;
        localStorage.setItem("lastActivity", now.toString());
      }
    };

    // Listen to user activity events
    const events = ["mousedown", "mousemove", "keypress", "scroll", "touchstart", "click"];
    events.forEach((event) => {
      window.addEventListener(event, updateActivity);
    });

    // Initialize activity timestamp
    updateActivity();

    // Check inactivity periodically every 5 seconds
    const intervalId = setInterval(checkInactivity, 5000);

    window.addEventListener("unauthorized-api-call", handleAuthError);
    return () => {
      clearInterval(intervalId);
      events.forEach((event) => {
        window.removeEventListener(event, updateActivity);
      });
      window.removeEventListener("unauthorized-api-call", handleAuthError);
    };
  }, [hasStaffToken, isLoginPage, router]);

  if (isLoginPage) {
    return <>{children}</>;
  }

  if (!hasStaffToken) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="text-center font-medium text-muted-foreground" role="status">
          Checking authorization...
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
