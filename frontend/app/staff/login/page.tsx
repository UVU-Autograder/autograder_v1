"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient, isMockApiEnabled } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";

type LoginResponse = {
  access_token: string;
  token_type: string;
  email: string;
  display_name: string | null;
  roles?: string[];
};

function getSafeReturnTo(target: string | null | undefined): string {
  if (target && target.startsWith("/staff") && !target.startsWith("/staff/login")) {
    return target;
  }
  return "/staff/courses";
}

export default function StaffLogin() {
  const router = useRouter();
  const [email, setEmail] = useState("dev.staff@uvu.edu");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  const isMockAllowed = isMockApiEnabled() || process.env.NEXT_PUBLIC_AUTH_PROVIDER !== "microsoft";

  useEffect(() => {
    if (typeof window === "undefined") return;

    const params = new URLSearchParams(window.location.search);
    const returnToParam = getSafeReturnTo(params.get("return_to"));

    // Check for auth_handoff cookie from Microsoft callback
    const cookieMatch = document.cookie.match(/(?:^|;\s*)auth_handoff=([^;]*)/);
    if (cookieMatch) {
      try {
        const handoffJson = decodeURIComponent(cookieMatch[1]);
        const data = JSON.parse(handoffJson) as {
          token: string;
          email: string;
          roles: string[];
          displayName?: string;
          returnTo?: string;
        };
        if (data.token) {
          localStorage.setItem("token", data.token);
          localStorage.setItem("email", data.email || "");
          localStorage.setItem("roles", JSON.stringify(data.roles || []));
          if (data.displayName) {
            localStorage.setItem("displayName", data.displayName);
          }
          // Invalidate handoff cookie immediately
          document.cookie = "auth_handoff=; Path=/; Max-Age=0; SameSite=Lax";
          window.dispatchEvent(new Event("roles-updated"));
          router.replace(getSafeReturnTo(data.returnTo || returnToParam));
          return;
        }
      } catch (e) {
        console.error("Failed to parse auth_handoff cookie:", e);
      }
    }

    const authToken = params.get("auth_token");
    const authError = params.get("error");
    const reason = params.get("reason");

    if (authToken) {
      const emailParam = params.get("email") || "";
      const rolesParam = params.get("roles") || "[]";
      const nameParam = params.get("name") || "";

      localStorage.setItem("token", authToken);
      localStorage.setItem("email", emailParam);
      localStorage.setItem("roles", rolesParam);
      if (nameParam) {
        localStorage.setItem("displayName", nameParam);
      }
      window.dispatchEvent(new Event("roles-updated"));
      router.replace(returnToParam);
      return;
    }

    if (authError) {
      void Promise.resolve().then(() => {
        if (
          authError === "pending_authorization" ||
          authError.toLowerCase().includes("pending staff authorization")
        ) {
          setError(
            "Account pending staff authorization. Please contact an administrator to request staff access."
          );
        } else if (authError === "missing_azure_credentials") {
          setError("Institutional Microsoft authentication is not configured on this host.");
        } else {
          setError(decodeURIComponent(authError));
        }
      });
    }

    if (reason === "timeout") {
      void Promise.resolve().then(() => {
        setInfoMessage("Your session has expired. Please sign in again.");
      });
    }

    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (token && !authError && !authToken) {
      router.replace(returnToParam);
    }
  }, [router]);

  const handleMicrosoftLogin = () => {
    setIsLoading(true);
    const params = new URLSearchParams(window.location.search);
    const returnTo = params.get("return_to");
    const qs = returnTo ? `?return_to=${encodeURIComponent(returnTo)}` : "";
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- API route performs 302 redirect to Microsoft Entra ID
    window.location.href = `/api/auth/microsoft/login${qs}`;
  };

  const handleMockSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail.endsWith("@uvu.edu")) {
      setError("Only @uvu.edu email addresses are allowed.");
      setIsLoading(false);
      return;
    }

    try {
      const data = await apiClient.post<LoginResponse>("/auth/mock-login", {
        email: trimmedEmail,
        display_name: null,
      });

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("email", data.email);
      localStorage.setItem("roles", JSON.stringify(data.roles ?? []));
      localStorage.setItem("lastActivity", Date.now().toString());
      if (data.display_name) {
        localStorage.setItem("displayName", data.display_name);
      }
      window.dispatchEvent(new Event("roles-updated"));
      window.dispatchEvent(new Event("storage"));

      const params = new URLSearchParams(window.location.search);
      const destination = getSafeReturnTo(params.get("return_to"));
      router.push(destination);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl font-bold">Staff Portal Sign In</CardTitle>
          <CardDescription>
            Authenticate with your institutional UVU Microsoft account.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {infoMessage && (
            <div className="rounded-lg border border-warning/30 bg-warning/10 p-3 text-sm text-warning font-medium">
              {infoMessage}
            </div>
          )}
          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive font-medium">
              {error}
            </div>
          )}

          {/* Primary Institutional Microsoft Sign-In */}
          <Button
            type="button"
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-2.5 flex items-center justify-center gap-2 shadow-sm"
            onClick={handleMicrosoftLogin}
            disabled={isLoading}
          >
            <svg className="w-4 h-4 fill-current" viewBox="0 0 21 21">
              <rect x="1" y="1" width="9" height="9" fill="#f25022" />
              <rect x="11" y="1" width="9" height="9" fill="#7fba00" />
              <rect x="1" y="11" width="9" height="9" fill="#00a4ef" />
              <rect x="11" y="11" width="9" height="9" fill="#ffb900" />
            </svg>
            Sign in with UVU Microsoft
          </Button>

          {/* Local Developer Mock Login (Only when allowed) */}
          {isMockAllowed && (
            <>
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">
                    Or Local Developer Sign In
                  </span>
                </div>
              </div>

              <form onSubmit={handleMockSubmit} className="flex flex-col gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@uvu.edu"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                  />
                </div>
                <Button
                  type="submit"
                  variant="outline"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? "Signing In..." : "Dev Mock Sign In"}
                </Button>
              </form>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
