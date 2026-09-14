"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
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

export default function StaffLogin() {
  const router = useRouter();
  const [email, setEmail] = useState("dev.staff@uvu.edu");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [infoMessage, setInfoMessage] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (token) {
      router.replace("/staff/courses");
      return;
    }

    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("reason") === "timeout") {
        void Promise.resolve().then(() => {
          setInfoMessage("Your session has expired due to 5 minutes of inactivity. Please sign in again.");
        });
      }
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
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
      window.dispatchEvent(new Event("roles-updated"));
      if (data.display_name) {
        localStorage.setItem("displayName", data.display_name);
      }

      router.push("/staff/courses");
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
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-2xl font-bold">Staff Portal Sign In</CardTitle>
            <CardDescription>
              Sign in with your UVU developer credentials for local testing.
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
            <div className="space-y-2">
              <Label htmlFor="email">
                Email Address
              </Label>
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
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Signing In..." : "Sign In"}
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  );
}
