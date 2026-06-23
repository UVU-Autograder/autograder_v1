"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

export function StaffAuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    Promise.resolve().then(() => {
      if (pathname === "/staff/login") {
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
    });

    const handleAuthError = () => {
      localStorage.removeItem("token");
      sessionStorage.removeItem("token");
      setIsAuthenticated(false);
      router.push("/staff/login");
    };

    window.addEventListener("unauthorized-api-call", handleAuthError);
    return () => {
      window.removeEventListener("unauthorized-api-call", handleAuthError);
    };
  }, [pathname, router]);

  if (isAuthenticated !== true) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-50">
        <div className="text-center font-medium text-slate-500">Checking authorization...</div>
      </div>
    );
  }

  return <>{children}</>;
}
