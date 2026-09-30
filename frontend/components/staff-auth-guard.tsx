"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

export function StaffAuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const isLoginPage = pathname === "/staff/login" || Boolean(pathname?.startsWith("/staff/login"));
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(() => {
    if (typeof window === "undefined") return null;
    if (window.location.pathname.startsWith("/staff/login")) return true;
    return Boolean(localStorage.getItem("token") || sessionStorage.getItem("token"));
  });

  useEffect(() => {
    if (isLoginPage) {
      setIsAuthenticated(true);
      return;
    }

    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (!token) {
      setIsAuthenticated(false);
      router.push("/staff/login");
    } else {
      setIsAuthenticated(true);
    }

    const handleAuthError = () => {
      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      localStorage.removeItem("lastActivity");
      setIsAuthenticated(false);
      router.push("/staff/login");
    };

    // Inactivity timeout: 60 minutes (3,600,000ms) to match standard session lifetime
    const INACTIVITY_TIMEOUT = 60 * 60 * 1000;

    const checkInactivity = () => {
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      if (!token || isLoginPage) return;

      const lastActivity = parseInt(localStorage.getItem("lastActivity") || "0");
      if (lastActivity === 0) return;

      const elapsed = Date.now() - lastActivity;
      if (elapsed >= INACTIVITY_TIMEOUT) {
        localStorage.removeItem("token");
        sessionStorage.removeItem("token");
        localStorage.removeItem("lastActivity");
        setIsAuthenticated(false);
        router.push("/staff/login?reason=timeout");
      }
    };

    let lastRecorded = 0;
    const updateActivity = () => {
      const now = Date.now();
      if (now - lastRecorded < 15000) return;
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      if (token && !isLoginPage) {
        lastRecorded = now;
        localStorage.setItem("lastActivity", now.toString());
      }
    };

    // Listen to user activity events
    const events = ["mousedown", "mousemove", "keypress", "scroll", "touchstart", "click"];
    events.forEach(event => {
      window.addEventListener(event, updateActivity);
    });

    // Initialize activity timestamp
    updateActivity();

    // Check inactivity periodically every 5 seconds
    const intervalId = setInterval(checkInactivity, 5000);

    window.addEventListener("unauthorized-api-call", handleAuthError);
    return () => {
      clearInterval(intervalId);
      events.forEach(event => {
        window.removeEventListener(event, updateActivity);
      });
      window.removeEventListener("unauthorized-api-call", handleAuthError);
    };
  }, [isLoginPage, pathname, router]);

  if (isLoginPage) {
    return <>{children}</>;
  }

  if (isAuthenticated !== true) {
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
