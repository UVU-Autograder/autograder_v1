"use client";

import { useEffect, useSyncExternalStore } from "react";
import { SunIcon, MoonIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function subscribeTheme(onStoreChange: () => void) {
  window.addEventListener("storage", onStoreChange);
  window.addEventListener("theme-updated", onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener("theme-updated", onStoreChange);
  };
}

function getThemeSnapshot(): "light" | "dark" {
  const stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function getThemeServerSnapshot(): "light" | "dark" {
  return "light";
}

function subscribeMounted(onStoreChange: () => void) {
  queueMicrotask(onStoreChange);
  return () => {};
}

export function ThemeToggle({ className }: { className?: string } = {}) {
  const mounted = useSyncExternalStore(
    subscribeMounted,
    () => true,
    () => false,
  );
  const theme = useSyncExternalStore(
    subscribeTheme,
    getThemeSnapshot,
    getThemeServerSnapshot,
  );

  useEffect(() => {
    if (!mounted) return;
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [mounted, theme]);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    localStorage.setItem("theme", nextTheme);
    window.dispatchEvent(new Event("theme-updated"));
  };

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className={cn("opacity-0 cursor-default", className)}
        aria-hidden="true"
        tabIndex={-1}
      />
    );
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      aria-label="Toggle theme"
      className={cn("text-muted-foreground hover:text-foreground cursor-pointer", className)}
    >
      {theme === "light" ? (
        <MoonIcon className="size-4" />
      ) : (
        <SunIcon className="size-4" />
      )}
    </Button>
  );
}
